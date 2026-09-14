import asyncio, tempfile, unittest
from pathlib import Path
from src.persistence import AOF
from src.store import Store

class PersistenceTests(unittest.IsolatedAsyncioTestCase):
    async def test_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            a = AOF(str(Path(d) / 'dump.aof'), False); s = Store(); await s.set('x','1'); a.append({'op':'SET','key':'x','value':'1','expire_at':None}); a.close()
            b = Store(); await AOF(str(Path(d) / 'dump.aof'), False).replay(b); self.assertEqual(await b.get('x'), '1')
