### 6.7 Geospatial Commands

| Command | Signature & Description | Success RESP Reply | Error RESP Reply | Example Usage & Return |
| :--- | :--- | :--- | :--- | :--- |
| `GEOADD` | `GEOADD key [NX\|XX] [CH] lon lat member [lon lat member ...]`<br>Adds geospatial coordinates. | `:<count_added>\r\n` | Coordinate errors | `GEOADD cities 13.361389 38.115556 "Palermo"` &rarr; `:1\r\n` |
| `GEODIST` | `GEODIST key member1 member2 [M\|KM\|FT\|MI]`<br>Returns distance between two members. | `$<len>\r\n<dist_str>\r\n` (or `$-1\r\n`) | Unit errors | `GEODIST cities Palermo Catania KM` &rarr; `$7\r\n166.2742\r\n` |
| `GEOHASH` | `GEOHASH key member [member ...]`<br>Returns Geohash string representations. | `*<count>\r\n$<len>\r\n<hash>...` | Arity errors | `GEOHASH cities Palermo` &rarr; `*1\r\n$11\r\nsqc8b49rny0\r\n` |
| `GEOPOS` | `GEOPOS key member [member ...]`<br>Returns longitude and latitude of members. | `*<count>\r\n*2\r\n$<len>\r\n<lon>\r\n$<len>\r\n<lat>...` | Arity errors | `GEOPOS cities Palermo` &rarr; `*1\r\n*2\r\n$9\r\n13.361389\r\n$9\r\n38.115556\r\n` |
| `GEORADIUS` | `GEORADIUS key lon lat radius M\|KM\|FT\|MI [WITHCOORD] [WITHDIST] [WITHHASH] [COUNT c] [ASC\|DESC]` | `*<results_array>\r\n` | Syntax/coordinate errors | `GEORADIUS cities 15 37 200 KM` &rarr; `*2\r\n$7\r\nPalermo\r\n$7\r\nCatania\r\n` |
| `GEORADIUSBYMEMBER` | `GEORADIUSBYMEMBER key member radius M\|KM\|FT\|MI [WITHCOORD] [WITHDIST] [WITHHASH] [COUNT c]` | `*<results_array>\r\n` | Syntax/member errors | `GEORADIUSBYMEMBER cities Palermo 200 KM` &rarr; `*2\r\n$7\r\nPalermo\r\n$7\r\nCatania\r\n` |
| `GEOSEARCH` | `GEOSEARCH key [FROMMEMBER m\|FROMLONLAT lon lat] [BYRADIUS r unit\|BYBOX w h unit] [ASC\|DESC]` | `*<results_array>\r\n` | Syntax/coordinate errors | `GEOSEARCH cities FROMLONLAT 15 37 BYRADIUS 200 KM` &rarr; `*2\r\n$7\r\nPalermo\r\n$7\r\nCatania\r\n` |
| `GEOSEARCHSTORE` | `GEOSEARCHSTORE dst src [FROMMEMBER m\|FROMLONLAT lon lat] [BYRADIUS r unit\|BYBOX w h unit] [STOREDIST]` | `:<count_stored>\r\n` | Syntax/coordinate errors | `GEOSEARCHSTORE out cities FROMLONLAT 15 37 BYRADIUS 200 KM` &rarr; `:2\r\n` |
