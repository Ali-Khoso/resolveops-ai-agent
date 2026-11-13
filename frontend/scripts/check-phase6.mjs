import assert from "node:assert/strict";
import {readFileSync,statSync} from "node:fs";
import {resolve} from "node:path";

const root=resolve(process.cwd(),"..");
const read=path=>readFileSync(resolve(root,path),"utf8");
const routes=["dashboard","tickets","insights","activity","docs","showcase","showcase/tickets","showcase/insights"];
for(const path of routes){
  const source=read(`frontend/src/app/${path}/page.tsx`);
  assert(source.includes("export default"),`Missing exported route: ${path}`);
}
const fixtures=read("frontend/src/lib/phase6-demo.ts");
assert(fixtures.includes("demo-only"),"Demo data must not use an actual Supabase owner");
assert(fixtures.includes("@example.test"),"Demo data must use non-routable sample emails");
assert(!fixtures.includes("service_role"),"Demo module must not contain service-role credentials");
const originalDocs=read("docs/screenshots/README.md");
for(const name of ["overview","tickets","insights"]){
  const path=`docs/screenshots/phase6-${name}.webp`;
  const bytes=readFileSync(resolve(root,path));
  assert(bytes.length>4000,`Screenshot too small: ${name}`);
  assert.equal(bytes.subarray(0,4).toString("ascii"),"RIFF");
  assert.equal(bytes.subarray(8,12).toString("ascii"),"WEBP");
  assert(originalDocs.includes(`phase6-${name}.webp`),`Unlinked preview: ${name}`);
}
assert(statSync(resolve(root,"docs/screenshots/phase6-ui-preview.html")).size>5000);
console.log("Phase 6 routes, synthetic fixtures, preview screenshots and gallery checks passed.");
