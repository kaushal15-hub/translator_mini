import json, csv, io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database.session import get_db
from app.database.models import User, Ticket, Room, RoomMember, Message, GlossaryTerm, AuditLog
from app.authentication.security import hash_password, verify_password, create_token, current_user, require_roles
from app.schemas import RegisterIn, LoginIn, TicketIn, TicketDecision, TranslateIn
from ai_engine.terminology.engine import TerminologyEngine
from ai_engine.terminology.engine import Term
from ai_engine.translation.fallback import DevelopmentFallback
from app.config import settings
router = APIRouter(prefix="/api")
LANGS = {"kn","en","hi","ml","ta"}
translator = DevelopmentFallback()
def glossary(db, domain):
    rows = db.scalars(select(GlossaryTerm).where(GlossaryTerm.domain==domain, GlossaryTerm.active==True)).all()
    return TerminologyEngine.from_records([{"term":r.term,"aliases":r.aliases,"case_sensitive":r.case_sensitive,"preserve_original":r.preserve_original,"priority":r.priority,"target_language":r.target_language} for r in rows])
@router.post("/auth/register")
def register(data: RegisterIn, db: Session=Depends(get_db)):
    if data.preferred_language not in LANGS: raise HTTPException(400,"Unsupported language")
    if db.scalar(select(User).where(User.email==data.email)): raise HTTPException(409,"Email already registered")
    u=User(email=data.email,password_hash=hash_password(data.password),preferred_language=data.preferred_language)
    db.add(u); db.commit(); db.refresh(u)
    return {"access_token":create_token(u.id),"token_type":"bearer","user":{"id":u.id,"email":u.email,"role":u.role}}
@router.post("/auth/login")
def login(data: LoginIn, db: Session=Depends(get_db)):
    u=db.scalar(select(User).where(User.email==data.email))
    if not u or not verify_password(data.password,u.password_hash): raise HTTPException(401,"Incorrect email or password")
    return {"access_token":create_token(u.id),"token_type":"bearer","user":{"id":u.id,"email":u.email,"role":u.role}}
@router.get("/auth/me")
def me(u: User=Depends(current_user)): return {"id":u.id,"email":u.email,"role":u.role,"preferred_language":u.preferred_language}
@router.post("/tickets")
def create_ticket(data: TicketIn, db: Session=Depends(get_db), u: User=Depends(current_user)):
    if data.source_language not in LANGS or data.target_language not in LANGS: raise HTTPException(400,"Unsupported language")
    if data.domain not in {"technology","medical","general"}: raise HTTPException(400,"Unknown domain")
    t=Ticket(creator_id=u.id,**data.model_dump()); db.add(t); db.commit(); db.refresh(t)
    return {"id":t.id,"status":t.status}
@router.get("/tickets")
def list_tickets(db: Session=Depends(get_db), u: User=Depends(current_user)):
    q=select(Ticket) if u.role=="admin" else select(Ticket).where(Ticket.creator_id==u.id)
    return [{"id":t.id,"creator_id":t.creator_id,"domain":t.domain,"source_language":t.source_language,"target_language":t.target_language,"status":t.status,"description":t.description} for t in db.scalars(q.order_by(Ticket.created_at.desc())).all()]
@router.post("/tickets/{ticket_id}/decision")
def decide(ticket_id:int,data:TicketDecision,db:Session=Depends(get_db),u:User=Depends(require_roles("admin"))):
    t=db.get(Ticket,ticket_id)
    if not t: raise HTTPException(404,"Ticket not found")
    if data.decision not in {"approve","reject"}: raise HTTPException(400,"decision must be approve or reject")
    t.status="Approved" if data.decision=="approve" else "Rejected"
    if data.agent_id:
        agent=db.get(User,data.agent_id)
        if not agent or agent.role not in {"agent","admin"}: raise HTTPException(400,"Invalid agent")
        t.assigned_agent_id=agent.id; t.status="Assigned"
    if data.decision=="approve" and not db.scalar(select(Room).where(Room.ticket_id==t.id)):
        room=Room(ticket_id=t.id,name=f"Ticket {t.id}")
        db.add(room); db.flush()
        for uid in {t.creator_id, u.id, *([t.assigned_agent_id] if t.assigned_agent_id else [])}: db.add(RoomMember(room_id=room.id,user_id=uid))
    db.add(AuditLog(actor_id=u.id,action="ticket_decision",details=f"ticket={t.id};decision={data.decision}"))
    db.commit(); return {"id":t.id,"status":t.status}
@router.get("/rooms")
def rooms(db:Session=Depends(get_db),u:User=Depends(current_user)):
    q=select(Room) if u.role=="admin" else select(Room).join(RoomMember).where(RoomMember.user_id==u.id)
    return [{"id":r.id,"ticket_id":r.ticket_id,"name":r.name} for r in db.scalars(q).all()]
@router.post("/translate")
async def translate(data:TranslateIn,db:Session=Depends(get_db),u:User=Depends(current_user)):
    engine=glossary(db,data.domain)
    protected, tokens=engine.protect(data.text,data.target_language)
    translated=await translator.translate(protected,data.source_language,data.target_language,data.domain,data.context[-4:])
    translated=engine.restore(translated,tokens)
    return {"original":data.text,"translated":translated,"mode":"development-fallback","warning":"Translation model is not configured; output is unchanged text, not an AI translation."}
@router.post("/admin/glossary/{domain}/upload")
async def upload_glossary(domain:str,file:UploadFile=File(...),db:Session=Depends(get_db),u:User=Depends(require_roles("admin"))):
    if domain not in {"technology","medical","general"}: raise HTTPException(400,"Unknown domain")
    raw=(await file.read()).decode("utf-8-sig")
    try:
        rows=json.loads(raw) if file.filename.lower().endswith(".json") else list(csv.DictReader(io.StringIO(raw)))
        if not isinstance(rows,list): raise ValueError("Expected a JSON array")
        for row in rows:
            aliases=row.get("aliases",[])
            if isinstance(aliases,str): aliases=[x.strip() for x in aliases.split("|") if x.strip()]
            db.add(GlossaryTerm(domain=domain,term=row["term"],aliases=aliases,source_language=row.get("source_language","*"),target_language=row.get("target_language") or None,case_sensitive=str(row.get("case_sensitive",False)).lower() in {"true","1"},preserve_original=str(row.get("preserve_original",True)).lower() not in {"false","0"},priority=int(row.get("priority",0)),active=str(row.get("active",True)).lower() not in {"false","0"}))
        db.add(AuditLog(actor_id=u.id,action="glossary_upload",details=f"domain={domain};rows={len(rows)}")); db.commit()
        return {"imported":len(rows)}
    except Exception as exc:
        db.rollback(); raise HTTPException(400,f"Invalid glossary file: {exc}")
@router.get("/admin/users")
def users(db:Session=Depends(get_db),u:User=Depends(require_roles("admin"))):
    return [{"id":x.id,"email":x.email,"role":x.role,"active":x.active} for x in db.scalars(select(User)).all()]
@router.post("/admin/users/{user_id}/role")
def set_role(user_id:int,role:str,db:Session=Depends(get_db),u:User=Depends(require_roles("admin"))):
    target=db.get(User,user_id)
    if not target: raise HTTPException(404,"User not found")
    if role not in {"user","agent","admin"}: raise HTTPException(400,"Invalid role")
    target.role=role; db.add(AuditLog(actor_id=u.id,action="role_change",details=f"user={user_id};role={role}")); db.commit()
    return {"id":target.id,"role":target.role}
