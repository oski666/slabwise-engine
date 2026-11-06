# Sticker dell'affidabilità (D191)

Metti in questa cartella **tre PNG con lo sfondo trasparente**, una per ogni livello di affidabilità dello Slabprice. Il sito le mette sopra le carte del catalogo e nella sezione "Quanto vale?" di ogni carta; se una PNG manca, il sito mostra la scritta di oggi.

| File | Livello | Quando appare |
|---|---|---|
| `fresche.png` | alto (oggi "Vendite fresche") | almeno 3 vendite proprie nelle ultime 13 settimane e SlabRange stretto |
| `stimato.png` | medio (oggi "Stimato") | poche vendite recenti: il prezzo viene anche dai voti vicini e dal mercato |
| `poco_sicuro.png` | basso (oggi "Poco sicuro") | SlabRange largo o vendite che non tornano tra loro |

Consigli: forma quadrata o tonda, almeno 256×256 px, leggibili anche a 32 px (nel catalogo stanno nell'angolo della carta). Il build le ritaglia, le rimpicciolisce e le incorpora nella pagina: i file originali non vengono toccati.

La legenda (cosa vuol dire ogni sticker) la scriviamo insieme quando ci sono i disegni.
