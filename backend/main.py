from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
from sqlalchemy import select
from app.config import settings
from app.database.session import Base, engine, SessionLocal
from app.database.models import User, Room, RoomMember, Message
from app.api.routes import router
from app.websocket.manager import manager
app=FastAPI(title=settings.app_name,version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.cors_origins.split(",")],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
app.include_router(router)
@app.on_event("startup")
def startup(): Base.metadata.create_all(bind=engine)
@app.get("/health")
def health(): return {"status":"ok","translation_mode":settings.translation_mode}
@app.websocket("/ws/rooms/{room_id}")
async def room_socket(ws:WebSocket,room_id:int,token:str=Query(...)):
    db=SessionLocal()
    try:
        try: uid=int(jwt.decode(token,settings.secret_key,algorithms=[settings.algorithm])["sub"])
        except (JWTError,ValueError,KeyError): await ws.close(code=4401); return
        user=db.get(User,uid); room=db.get(Room,room_id)
        allowed=user and room and (user.role=="admin" or db.scalar(select(RoomMember).where(RoomMember.room_id==room_id,RoomMember.user_id==uid)))
        if not allowed: await ws.close(code=4403); return
        await manager.connect(room_id,ws)
        await manager.broadcast(room_id,{"type":"presence","status":"connected"})
        while True:
            data=await ws.receive_json()
            text=str(data.get("text","")).strip()
            if not text or len(text)>10000: await ws.send_json({"error":"Message must contain 1-10000 characters"}); continue
            ticket=db.get(__import__("app.database.models",fromlist=["Ticket"]).Ticket,room.ticket_id)
            from ai_engine.terminology.engine import TerminologyEngine
            from app.api.routes import glossary,translator
            engine=glossary(db,ticket.domain)
            protected,tokens=engine.protect(text,ticket.target_language)
            translated=await translator.translate(protected,ticket.source_language,ticket.target_language,ticket.domain,[])
            translated=engine.restore(translated,tokens)
            msg=Message(room_id=room_id,sender_id=uid,original_text=text,translated_text=translated,source_language=ticket.source_language,target_language=ticket.target_language,domain=ticket.domain,translation_mode="development-fallback")
            db.add(msg); db.commit(); db.refresh(msg)
            await manager.broadcast(room_id,{"type":"message","id":msg.id,"sender_id":uid,"original":text,"translated":translated,"domain":ticket.domain,"source_language":ticket.source_language,"target_language":ticket.target_language,"timestamp":msg.created_at.isoformat(),"mode":"development-fallback"})
    except WebSocketDisconnect: pass
    finally:
        manager.disconnect(room_id,ws); db.close()
