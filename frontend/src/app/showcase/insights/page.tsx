import "../../phase6.css";
import Phase6Shell from "@/components/phase6/shell";
import Insights from "@/components/phase6/insights";
import DemoTabs from "@/components/phase6/demo-tabs";
import {demoOverview} from "@/lib/phase6-demo";
export const metadata={title:"Insights preview — ResolveOps",robots:{index:false,follow:false}};
export default function ShowcaseInsights(){
 return <Phase6Shell active="/insights" eyebrow="EXPLORE THE EXPERIENCE" title="Operations insights"
  description="Explore sample support metrics and reviewer outcomes." demo>
  <DemoTabs/><Insights data={demoOverview}/>
 </Phase6Shell>;
}
