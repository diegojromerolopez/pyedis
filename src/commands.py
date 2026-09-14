"""Redis command dispatcher."""
from __future__ import annotations
import time
from .resp import bulk, error, integer, simple, array
from .store import Store
from .persistence import AOF

class Dispatcher:
    def __init__(self, store: Store, aof: AOF | None = None) -> None:
        self.store = store; self.aof = aof

    def _log(self, record: dict[str, object]) -> None:
        if self.aof is not None: self.aof.append(record)

    async def dispatch(self, raw: list[bytes]) -> tuple[bytes, bool]:
        if not raw: return error('ERR empty command'), False
        cmd = raw[0].decode(errors='replace').upper(); args = [x.decode(errors='replace') for x in raw[1:]]
        def arity(n: int | tuple[int, ...]) -> bytes | None:
            if len(args) not in (n if isinstance(n, tuple) else (n,)): return error(f"ERR wrong number of arguments for '{cmd.lower()}' command")
            return None
        if cmd == 'PING':
            if len(args) > 1: return error("ERR wrong number of arguments for 'ping' command"), False
            return (simple('PONG') if not args else bulk(args[0])), False
        if cmd == 'ECHO':
            e = arity(1)
            return (e or bulk(args[0])), False
        if cmd == 'QUIT':
            e = arity(0); return (e or simple('OK')), not bool(e)
        if cmd == 'SET':
            if len(args) < 2: return error("ERR wrong number of arguments for 'set' command"), False
            key, value = args[:2]; nx = xx = False; expiry = None; i = 2
            while i < len(args):
                flag = args[i].upper()
                if flag in ('NX','XX'):
                    if flag == 'NX': nx = True
                    else: xx = True
                    i += 1; continue
                if flag in ('EX','PX') and i + 1 < len(args):
                    try: number = int(args[i + 1])
                    except ValueError: number = 0
                    if number <= 0: return error('ERR value is not an integer or out of range'), False
                    expiry = self.store.clock() + (number if flag == 'EX' else number / 1000); i += 2; continue
                return error('ERR syntax error'), False
            if nx and xx: return error('ERR syntax error'), False
            ok = await self.store.set(key, value, expiry, nx, xx)
            if ok: self._log({'op':'SET','key':key,'value':value,'expire_at':expiry})
            return (simple('OK') if ok else bulk(None)), False
        if cmd in ('GET','DEL','EXISTS','INCR','DECR','EXPIRE','TTL','KEYS'):
            expected = {'GET':1,'DEL':None,'EXISTS':None,'INCR':1,'DECR':1,'EXPIRE':2,'TTL':1,'KEYS':1}[cmd]
            if expected is not None and len(args) != expected or expected is None and not args: return error(f"ERR wrong number of arguments for '{cmd.lower()}' command"), False
        if cmd == 'GET': return bulk(await self.store.get(args[0])), False
        if cmd == 'DEL':
            n = await self.store.delete(args); [self._log({'op':'DEL','key':k}) for k in args]
            return integer(n), False
        if cmd == 'EXISTS': return integer(sum(await self.store.exists(k) for k in args)), False
        if cmd in ('INCR','DECR'):
            n, ok = await self.store.increment(args[0], 1 if cmd == 'INCR' else -1)
            if not ok: return error('ERR value is not an integer or out of range'), False
            self._log({'op':cmd,'key':args[0]}); return integer(n), False
        if cmd == 'EXPIRE':
            try: seconds = int(args[1])
            except ValueError: return error('ERR value is not an integer or out of range'), False
            ok = await self.store.expire(args[0], seconds)
            if ok: self._log({'op':'EXPIRE','key':args[0],'expire_at':self.store.clock()+seconds})
            return integer(int(ok)), False
        if cmd == 'TTL': return integer(await self.store.ttl(args[0])), False
        if cmd == 'KEYS': return array([bulk(k) for k in await self.store.keys(args[0])]), False
        if cmd == 'FLUSHALL':
            if args: return error("ERR wrong number of arguments for 'flushall' command"), False
            await self.store.flush(); self._log({'op':'FLUSHALL'}); return simple('OK'), False
        if cmd in ('COMMAND','INFO','CLIENT'): return array([]), False
        return error(f"ERR unknown command '{raw[0].decode(errors='replace')}'"), False
