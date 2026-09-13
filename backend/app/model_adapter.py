from __future__ import annotations

import asyncio
import json
import os
import urllib.request
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Protocol

@dataclass
class ModelRequest:
    goal: str
    memories: list[dict[str, Any]] = field(default_factory=list)
    available_tools: list[dict[str, Any]] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)

@dataclass
class ModelResponse:
    model_id: str
    action: str
    reason: str
    confidence: float
    suggested_tools: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

class BrainModel(Protocol):
    model_id: str
    async def generate(self, request: ModelRequest) -> ModelResponse: ...

class LocalDeterministicModel:
    model_id = "local-deterministic-v2.2"
    async def generate(self, request: ModelRequest) -> ModelResponse:
        goal = request.goal.strip(); tools = {item.get("name") for item in request.available_tools}
        suggested = [tool for tool in ("echo", "clock") if tool in tools]
        confidence = 0.92 if goal and suggested else 0.40
        if any(memory.get("kind") == "failure" for memory in request.memories): confidence = max(0.70, confidence - 0.10)
        return ModelResponse(self.model_id, "execute_guarded_plan", "Built-in offline System 2 proposed; System 1 remains authoritative.", confidence, suggested, {"provider":"builtin","role":"system2","network":False,"external_api":False})

class BuiltinSystem1Guard:
    model_id = "system1-local-guard"
    provider = "builtin"
    async def generate(self, request: ModelRequest) -> ModelResponse:
        risky = {t.get("name") for t in request.available_tools if t.get("risk") in {"HIGH", "CRITICAL"}}
        return ModelResponse(self.model_id, "allow_guarded_execution", "Built-in deterministic System 1 guard validated the proposal boundary; authorization remains mandatory.", 0.99 if not risky else 0.80, [], {"provider":"builtin","role":"system1","network":False,"external_api":False})

class OpenAICompatibleLocalModel:
    def __init__(self, model_id: str, base_url: str, model_name: str, timeout: float = 60.0): self.model_id,self.base_url,self.model_name,self.timeout=model_id,base_url.rstrip("/"),model_name,timeout
    async def generate(self, request: ModelRequest) -> ModelResponse:
        payload={"model":self.model_name,"messages":[{"role":"system","content":"You are System 2. Propose only. Never execute tools."},{"role":"user","content":build_local_prompt(request)}],"temperature":0.1,"stream":False}
        data=await asyncio.to_thread(http_json,self.base_url+"/v1/chat/completions",payload,self.timeout,None)
        return parse_model_text(self.model_id,extract_openai_text(data),"local_server","system2")

class RemoteOpenAIModel:
    model_id="system1-openai"; provider="openai"
    async def generate(self, request: ModelRequest)->ModelResponse:
        key=os.getenv("OPENAI_API_KEY")
        if not key: raise RuntimeError("provider_not_configured:openai")
        payload={"model":os.getenv("AGENTIC_OPENAI_MODEL","gpt-4.1-mini"),"messages":[{"role":"system","content":"You are System 1. Review proposals only; never execute tools. Return JSON: {action,reason,confidence,suggested_tools}."},{"role":"user","content":build_local_prompt(request)}],"temperature":0,"stream":False}
        data=await asyncio.to_thread(http_json,"https://api.openai.com/v1/chat/completions",payload,60,{"Authorization":f"Bearer {key}"})
        return parse_model_text(self.model_id,extract_openai_text(data),"openai","system1")

class RemoteGeminiModel:
    model_id="system1-gemini"; provider="google"
    async def generate(self, request: ModelRequest)->ModelResponse:
        key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not key: raise RuntimeError("provider_not_configured:gemini")
        model=os.getenv("AGENTIC_GEMINI_MODEL","gemini-2.5-flash")
        payload={"contents":[{"parts":[{"text":"You are System 1. Review this proposal for safety and correctness. Return JSON with action,reason,confidence,suggested_tools.\n"+build_local_prompt(request)}]}]}
        data=await asyncio.to_thread(http_json,f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",payload,60,None)
        return parse_model_text(self.model_id,data["candidates"][0]["content"]["parts"][0]["text"],"google","system1")

class RemoteAnthropicModel:
    model_id="system1-anthropic"; provider="anthropic"
    async def generate(self, request: ModelRequest)->ModelResponse:
        key=os.getenv("ANTHROPIC_API_KEY")
        if not key: raise RuntimeError("provider_not_configured:anthropic")
        payload={"model":os.getenv("AGENTIC_ANTHROPIC_MODEL","claude-sonnet-4-20250514"),"max_tokens":512,"system":"You are System 1. Review proposals only; never execute tools. Return JSON with action,reason,confidence,suggested_tools.","messages":[{"role":"user","content":build_local_prompt(request)}]}
        data=await asyncio.to_thread(http_json,"https://api.anthropic.com/v1/messages",payload,60,{"x-api-key":key,"anthropic-version":"2023-06-01"})
        return parse_model_text(self.model_id,data["content"][0]["text"],"anthropic","system1")

def build_local_prompt(request: ModelRequest)->str:
    tools=[{"name":t.get("name"),"risk":t.get("risk"),"policy":t.get("policy")} for t in request.available_tools]
    return json.dumps({"goal":request.goal,"memories":request.memories[-8:],"available_tools":tools,"constraints":request.constraints},ensure_ascii=False)

def parse_model_text(model_id:str,text:str,provider:str,role:str)->ModelResponse:
    raw=text.strip()
    if raw.startswith("```"): raw=raw.strip("`").replace("json\n","",1).strip()
    try: obj=json.loads(raw)
    except json.JSONDecodeError: return ModelResponse(model_id,"review",text[:1000],0.50,[],{"provider":provider,"role":role,"structured":False})
    return ModelResponse(model_id,str(obj.get("action","review")),str(obj.get("reason","")),max(0,min(1,float(obj.get("confidence",.5)))),[str(x) for x in obj.get("suggested_tools",[])],{"provider":provider,"role":role,"structured":True})

def extract_openai_text(data:dict[str,Any])->str: return str(data["choices"][0]["message"]["content"])
def http_json(url:str,payload:dict[str,Any],timeout:float,headers:dict[str,str]|None)->dict[str,Any]:
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),method="POST",headers={"Content-Type":"application/json",**(headers or {})})
    with urllib.request.urlopen(req,timeout=timeout) as response: return json.loads(response.read().decode())

@dataclass
class ModelRuntime:
    active_system2:str="local-deterministic-v2.2"
    system1_enabled:bool=True
    timeout_seconds:float=60.0
    fallback_enabled:bool=True
    provider_stats:dict[str,dict[str,Any]]=field(default_factory=dict)
    def status(self)->dict[str,Any]: return {"active_system2":self.active_system2,"system1_enabled":self.system1_enabled,"timeout_seconds":self.timeout_seconds,"fallback_enabled":self.fallback_enabled,"system2_network_policy":"loopback_only","system2_role":"local_only","system1_provider_stats":self.provider_stats}
    def record_provider(self, model_id:str, status:str, latency_ms:int=0, error:str|None=None)->None:
        item=self.provider_stats.setdefault(model_id,{"calls":0,"successes":0,"errors":0,"last_status":"never","last_latency_ms":0,"last_error":None})
        item["calls"]+=1; item["last_status"]=status; item["last_latency_ms"]=latency_ms; item["last_error"]=error
        if status=="ok": item["successes"]+=1
        elif status=="error": item["errors"]+=1

runtime=ModelRuntime()
_system2:dict[str,BrainModel]={"local-deterministic-v2.2":LocalDeterministicModel()}
_system1:dict[str,BrainModel]={"system1-local-guard":BuiltinSystem1Guard(),"system1-openai":RemoteOpenAIModel(),"system1-gemini":RemoteGeminiModel(),"system1-anthropic":RemoteAnthropicModel()}

def register_local_system2(model_id:str,base_url:str,model_name:str)->dict[str,Any]:
    if not base_url.startswith(("http://127.0.0.1","http://localhost","http://[::1]")): raise ValueError("system2_local_only:base_url_must_be_loopback")
    _system2[model_id]=OpenAICompatibleLocalModel(model_id,base_url,model_name); return get_model_info(model_id)

def list_models()->list[dict[str,Any]]: return [get_model_info(mid) for mid in _system2]
def list_system1_models()->list[dict[str,Any]]:
    return [{"model_id":mid,"role":"system1","provider":getattr(m,"provider","local"),"configured":is_configured(mid),"available":True,"health":runtime.provider_stats.get(mid,{"last_status":"never","calls":0,"successes":0,"errors":0})} for mid,m in _system1.items()]
def is_configured(model_id:str)->bool:
    if model_id=="system1-openai": return bool(os.getenv("OPENAI_API_KEY"))
    if model_id=="system1-gemini": return bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
    if model_id=="system1-anthropic": return bool(os.getenv("ANTHROPIC_API_KEY"))
    return model_id in _system1 or model_id in _system2

def get_model_info(model_id:str)->dict[str,Any]:
    model=_system2[model_id]
    return {"model_id":model_id,"role":"system2","kind":"local","active":model_id==runtime.active_system2,"configured":is_configured(model_id),"network":isinstance(model,OpenAICompatibleLocalModel),"external_api":False,"system1_authority":True}

def get_model(model_id:str|None=None)->BrainModel:
    selected=model_id or runtime.active_system2
    if selected not in _system2: raise ValueError(f"system2_model_not_found:{selected}")
    return _system2[selected]
def set_active_model(model_id:str)->dict[str,Any]: get_model(model_id); runtime.active_system2=model_id; return runtime.status()

async def system1_review(request:ModelRequest,providers:list[str]|None=None)->dict[str,Any]:
    selected=providers or list(_system1); reviews=[]
    for provider_id in selected:
        model=_system1.get(provider_id)
        if not model or not is_configured(provider_id):
            reviews.append({"model_id":provider_id,"status":"not_configured"}); runtime.record_provider(provider_id,"not_configured"); continue
        started=perf_counter()
        try:
            result=await asyncio.wait_for(model.generate(request),timeout=runtime.timeout_seconds)
            latency=int((perf_counter()-started)*1000); runtime.record_provider(provider_id,"ok",latency)
            reviews.append({"model_id":result.model_id,"status":"ok","action":result.action,"reason":result.reason,"confidence":result.confidence,"suggested_tools":result.suggested_tools,"metadata":result.metadata,"latency_ms":latency})
        except Exception as exc:
            latency=int((perf_counter()-started)*1000); runtime.record_provider(provider_id,"error",latency,str(exc))
            reviews.append({"model_id":provider_id,"status":"error","error":str(exc),"latency_ms":latency})
    ok=[r for r in reviews if r.get("status")=="ok"]
    # Safe fallback is System 1 only: the built-in guard may provide an additional review.
    if runtime.fallback_enabled and not ok and "system1-local-guard" not in selected:
        fallback=_system1["system1-local-guard"]
        started=perf_counter()
        try:
            result=await asyncio.wait_for(fallback.generate(request),timeout=runtime.timeout_seconds)
            latency=int((perf_counter()-started)*1000); runtime.record_provider("system1-local-guard","ok",latency)
            reviews.append({"model_id":result.model_id,"status":"ok","action":result.action,"reason":"safe System 1 fallback: "+result.reason,"confidence":result.confidence,"suggested_tools":result.suggested_tools,"metadata":result.metadata|{"fallback":True},"latency_ms":latency})
            ok=[r for r in reviews if r.get("status")=="ok"]
        except Exception as exc:
            runtime.record_provider("system1-local-guard","error",int((perf_counter()-started)*1000),str(exc))
    allowed=bool(ok) and all(r.get("confidence",0)>=0.5 for r in ok)
    return {"allowed":allowed,"reviews":reviews,"configured_count":len(ok),"decision":"allow" if allowed else "escalate","fallback_used":any(r.get("metadata",{}).get("fallback") for r in reviews)}
