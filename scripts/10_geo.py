"""Census cartographic boundary shapefiles → 精簡 GeoJSON（119 屆國會選區 5m、郡 20m），座標取 3 位小數，供儀表板內嵌。"""
import zipfile, json, shapefile, io
from common import *
def shp2geojson(zf, idfield, name):
    z=zipfile.ZipFile(RAW/'geo'/zf); base=[n for n in z.namelist() if n.endswith('.shp')][0][:-4]
    r=shapefile.Reader(shp=io.BytesIO(z.read(base+'.shp')), dbf=io.BytesIO(z.read(base+'.dbf')), shx=io.BytesIO(z.read(base+'.shx')))
    fields=[f[0] for f in r.fields[1:]]; feats=[]
    def rnd(c):
        if isinstance(c[0],(float,int)): return [round(c[0],3),round(c[1],3)]
        return [rnd(x) for x in c]
    for sr in r.shapeRecords():
        rec=dict(zip(fields,sr.record)); g=sr.shape.__geo_interface__
        feats.append({'type':'Feature','id':rec[idfield],'properties':{'STATEFP':rec.get('STATEFP'),'NAME':rec.get('NAME') or rec.get('NAMELSAD'),'CD':rec.get('CD119FP')},'geometry':{'type':g['type'],'coordinates':rnd(g['coordinates'])}})
    out={'type':'FeatureCollection','features':feats}; (CLEAN/f'{name}.geojson').write_text(json.dumps(out,separators=(',',':'))); print(name, len(feats), 'features', round((CLEAN/f'{name}.geojson').stat().st_size/1e6,1),'MB', fields)
shp2geojson('cb_2024_us_cd119_5m.zip','GEOID','geo_cd119')
shp2geojson('cb_2024_us_county_20m.zip','GEOID','geo_county')
