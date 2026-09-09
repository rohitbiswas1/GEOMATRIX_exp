'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { projects, riskLevel } from '../../lib/data';
import { Layers, Search, SlidersHorizontal } from 'lucide-react';

type GoogleMap = any;
type GoogleMarker = any;

function loadGoogleMaps(apiKey: string): Promise<any> {
  return new Promise((resolve, reject) => {
    const w = window as any;
    if (w.google?.maps) return resolve(w.google.maps);
    const existing = document.querySelector('script[data-geomatrix-google-maps="true"]') as HTMLScriptElement | null;
    if (existing) {
      existing.addEventListener('load', () => resolve(w.google.maps));
      existing.addEventListener('error', reject);
      return;
    }
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(apiKey)}&v=weekly`;
    script.async = true;
    script.defer = true;
    script.dataset.geomatrixGoogleMaps = 'true';
    script.onload = () => w.google?.maps ? resolve(w.google.maps) : reject(new Error('Google Maps API did not initialize'));
    script.onerror = () => reject(new Error('Unable to load Google Maps'));
    document.head.appendChild(script);
  });
}

export default function MapPage() {
  const ref = useRef<HTMLDivElement>(null);
  const mapRef = useRef<GoogleMap>(null);
  const markersRef = useRef<GoogleMarker[]>([]);
  const [selected, setSelected] = useState<typeof projects[0] | null>(null);
  const [mapReady, setMapReady] = useState(false);
  const [mapFailed, setMapFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function init() {
      if (!ref.current || mapRef.current) return;
      const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
      if (!apiKey) {
        setMapFailed(true);
        return;
      }
      try {
        const googleMaps = await loadGoogleMaps(apiKey);
        if (cancelled || !ref.current) return;

        const map = new googleMaps.Map(ref.current, {
          center: { lat: 22.5, lng: 82.5 },
          zoom: 5,
          mapTypeControl: true,
          streetViewControl: false,
          fullscreenControl: true,
          zoomControl: true,
        });

        markersRef.current = projects.map((p) => {
          const color = p.risk >= 75 ? '#c43d3d' : p.risk >= 50 ? '#d8872c' : p.risk >= 25 ? '#d7a20c' : '#16845b';
          const marker = new googleMaps.Marker({
            map,
            position: { lat: p.lat, lng: p.lng },
            title: p.name,
            icon: {
              path: googleMaps.SymbolPath.CIRCLE,
              scale: 8,
              fillColor: color,
              fillOpacity: 1,
              strokeColor: '#ffffff',
              strokeWeight: 2,
            },
          });
          marker.addListener('click', () => setSelected(p));
          return marker;
        });

        mapRef.current = map;
        setMapReady(true);
      } catch {
        if (!cancelled) setMapFailed(true);
      }
    }

    init();
    return () => {
      cancelled = true;
      markersRef.current.forEach((m) => m.setMap?.(null));
      markersRef.current = [];
      if (mapRef.current) {
        mapRef.current = null;
      }
    };
  }, []);

  return (
    <div className="page"><div className="maplayout">
      <section className="mapbox">
        <div ref={ref} className="mapcanvas" />
        {!mapReady && !mapFailed && <div className="mapfallback"><div><Layers size={40}/><h3>Loading Google Maps…</h3><div className="sub">Preparing the interactive project-risk map.</div></div></div>}
        {mapFailed && <div className="mapfallback"><div><Layers size={40}/><h3>Google Maps configuration required</h3><div className="sub">Add NEXT_PUBLIC_GOOGLE_MAPS_API_KEY in Vercel, enable Maps JavaScript API and billing, then redeploy.</div></div></div>}
        {selected && <div style={{position:'absolute',left:18,bottom:18,width:290,background:'#fff',border:'1px solid var(--line)',padding:14,borderRadius:6,boxShadow:'0 8px 25px #0002',zIndex:1000}}><div className="eyebrow">Project preview</div><h3 style={{fontSize:14,margin:'6px 0'}}>{selected.name}</h3><div className="sub">{selected.state} · {selected.district}</div><div style={{display:'flex',justifyContent:'space-between',margin:'12px 0'}}><span className={'risk '+riskLevel(selected.risk).toLowerCase()}>{riskLevel(selected.risk)} {selected.risk}/100</span><b>{selected.delay}% delay</b></div><div className="muted">Main driver: {selected.driver}</div><Link className="btn primary" style={{display:'inline-block',marginTop:12}} href={'/projects/'+selected.id}>Open Project</Link></div>}
        <div style={{position:'absolute',left:14,top:14,zIndex:900,background:'#fff',border:'1px solid var(--line)',borderRadius:5,padding:'6px 9px',fontSize:11,fontWeight:600,boxShadow:'0 2px 8px #0001'}}>Google Maps GIS</div>
      </section>
      <aside className="mapside"><div className="eyebrow">GIS Risk Intelligence</div><h2 style={{fontSize:20,margin:'5px 0'}}>Spatial risk overview</h2><div className="search" style={{maxWidth:'none',margin:'14px 0'}}><Search size={14}/><input placeholder="Search map projects…"/></div><div className="mapmetric"><div><div className="muted">Total projects</div><b>128</b></div><div><div className="muted">Critical</div><b>12</b></div><div><div className="muted">High-risk</div><b>27</b></div><div><div className="muted">Affected area</div><b>18.4k ha</b></div></div><div className="panel" style={{padding:12}}><div className="paneltitle"><SlidersHorizontal size={13}/> Filters</div><div className="form" style={{marginTop:10}}><select><option>All States</option></select><select><option>All Districts</option></select><select><option>All Risk Levels</option></select><select><option>All Acquisition Stages</option></select><select><option>All Project Types</option></select></div></div><div style={{marginTop:18}}><div className="paneltitle">Layers</div><div className="legend"><div className="legendrow"><span className="legenddot" style={{background:'#c43d3d'}}/> Critical projects</div><div className="legendrow"><span className="legenddot" style={{background:'#d8872c'}}/> High-risk projects</div><div className="legendrow"><span className="legenddot" style={{background:'#d7a20c'}}/> Medium-risk projects</div><div className="legendrow"><span className="legenddot" style={{background:'#16845b'}}/> Low-risk projects</div></div></div><p className="footer-note">Powered by Google Maps. The map uses the public browser key configured as NEXT_PUBLIC_GOOGLE_MAPS_API_KEY.</p></aside>
    </div></div>
  );
}
