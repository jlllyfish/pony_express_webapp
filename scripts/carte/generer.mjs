// Fond de carte Europe (SVG) : chemins pré-projetés, propriétés iso2 + nom FR
import fs from "fs";
import { feature } from "topojson-client";
import { geoConicConformal, geoPath } from "d3-geo";
import countries from "i18n-iso-countries";
import fr from "i18n-iso-countries/langs/fr.json" with { type: "json" };
countries.registerLocale(fr);
const topo = JSON.parse(fs.readFileSync("node_modules/world-atlas/countries-50m.json"));
const geo = feature(topo, topo.objects.countries);
const W = 800, H = 640;
// cadrage : de l'Islande / Canaries à la mer Noire, du Maghreb au Cap Nord
const cadre = { type: "MultiPoint", coordinates: [[-24, 36], [42, 36], [-10, 71], [32, 71], [-17, 35], [40, 44], [10, 34.5]] };
const proj = geoConicConformal().rotate([-10, 0]).parallels([40, 62])
  .fitExtent([[10, 10], [W - 10, H - 10]], cadre);
proj.clipExtent([[0, 0], [W, H]]);
const path = geoPath(proj).digits(1);
const pays = [];
for (const f of geo.features) {
  const num = String(f.id ?? "").padStart(3, "0");
  let iso2 = countries.numericToAlpha2(num);
  if (!iso2 && f.properties.name === "Kosovo") iso2 = "XK";
  if (!iso2) continue;
  const d = path(f);
  if (!d) continue;
  const [[x0, y0], [x1, y1]] = path.bounds(f);
  if (x1 < 0 || y1 < 0 || x0 > W || y0 > H) continue;
  pays.push({ iso2, nom: countries.getName(iso2, "fr") || f.properties.name, d });
}
// noms français de tous les pays (pour les mobilités hors du cadre de la carte)
const noms = countries.getNames("fr", { select: "official" });
noms.XK = "Kosovo";
fs.writeFileSync("europe.json", JSON.stringify({ largeur: W, hauteur: H, pays, noms }));
console.log(pays.length, "pays", (fs.statSync("europe.json").size / 1024).toFixed(0), "Ko");
