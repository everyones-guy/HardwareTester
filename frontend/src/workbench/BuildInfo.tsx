import {useEffect,useState} from 'react';
declare const __BUILD_INFO__: {version:string;build:string;builtAt:string};
export default function BuildInfo(){
  const [backend,setBackend]=useState<{version:string;build:string;deployment:string;instance:string;apiOrigin:string;authEnabled:boolean}>();
  useEffect(()=>{fetch('/api/version').then(r=>r.ok?r.json():undefined).then(setBackend).catch(()=>{});},[]);
  return <section className="panel settings-panel" style={{marginTop:24}}><h2>Environment and build</h2><dl><div><dt>This browser</dt><dd>{window.location.origin}</dd></div><div><dt>Frontend</dt><dd>{__BUILD_INFO__.version} · {__BUILD_INFO__.build}</dd></div><div><dt>Frontend built</dt><dd>{new Date(__BUILD_INFO__.builtAt).toLocaleString()}</dd></div><div><dt>Backend</dt><dd>{backend?`${backend.version} · ${backend.build}`:'Unavailable'}</dd></div><div><dt>Backend address</dt><dd>{backend?.apiOrigin||'Unavailable'}</dd></div><div><dt>Deployment</dt><dd>{backend?.deployment||'Unknown'}</dd></div><div><dt>Workspace instance</dt><dd>{backend?.instance||'Unknown'}</dd></div><div><dt>Access control</dt><dd>{backend?.authEnabled?'Accounts and roles enabled':'Local development mode'}</dd></div></dl></section>;
}
