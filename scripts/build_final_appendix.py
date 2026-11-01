"""Six analytical exhibits. Each supports a slide claim with method, result and boundary."""
from pathlib import Path
import json, math
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.comments import Comment
from openpyxl.chart import BarChart, Reference
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.worksheet.pagebreak import Break
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/final_release_v1/VOLT-FORGE_Final_Appendix.xlsx'
def load(p):return json.loads((ROOT/p).read_text())
summary=load('reports/final_release_v1/study/summary.json')
cases=[json.loads(l) for l in (ROOT/'reports/final_release_v1/study/cases.jsonl').read_text().splitlines()]
measured=load('reports/measured_comparison_v1/final/result.json')['cases']
engineering=load('reports/engineering_checks_v1/result.json')
cost=load('configs/build_cost_v1.json'); market=load('configs/market_sizing_v1.json')
verify=load('reports/final_release_v1/verification.json')
wb=Workbook();wb.remove(wb.active)
NAVY='102D46';BLUE='0B6FA8';LIGHT='E7F2F8';INK='10202F';GREY='526272';ORANGE='9B4A26';AMBER='FFF0DD';WHITE='FFFFFF'
names=['A1 Decision','A2 Sizing','A3 Data pedigree','A4 Accuracy','A5 Sensitivity','A6 Economics']
urls='https://github.com/shu-aro/VOLT-FORGE/blob/v4/'

def text(ws,r,s,first=1,last=12,bold=False,size=11,color=INK,fill=None,height=31):
 ws.merge_cells(start_row=r,start_column=first,end_row=r,end_column=last)
 c=ws.cell(r,first,s);c.font=Font(name='Arial',size=size,bold=bold,color=color);c.alignment=Alignment(wrap_text=True,vertical='center')
 if fill:
  for row in ws.iter_rows(min_row=r,max_row=r,min_col=first,max_col=last):
   for x in row:x.fill=PatternFill('solid',fgColor=fill)
 ws.row_dimensions[r].height=height
 return c

def source(ws,r,label,path):
 c=text(ws,r,'Source: '+label,size=9,color=GREY,height=25)
 c.hyperlink=path if path.startswith('http') else urls+path;c.font=Font(name='Arial',size=9,color=BLUE,underline='single')

def sheet(index,title,question,claim):
 ws=wb.create_sheet(names[index]);ws.sheet_view.showGridLines=False;ws.sheet_view.zoomScale=85
 for col in 'ABCDEFGHIJKL':ws.column_dimensions[col].width=12.2
 text(ws,1,f'A{index+1}  |  {title}',bold=True,size=19,color=WHITE,fill=NAVY,height=44)
 for i,n in enumerate(names):
  a=i*2+1;ws.merge_cells(start_row=2,start_column=a,end_row=2,end_column=a+1)
  c=ws.cell(2,a,n);c.hyperlink=f"#'{n}'!A1";c.font=Font(name='Arial',size=9,color=BLUE,bold=True);c.alignment=Alignment(horizontal='center')
 ws.row_dimensions[2].height=25
 text(ws,4,question,bold=True,size=14,height=34)
 text(ws,5,claim,size=11,fill=LIGHT,height=42)
 ws.freeze_panes='C8';ws.sheet_properties.pageSetUpPr.fitToPage=True
 ws.page_setup.orientation='portrait';ws.page_setup.paperSize=ws.PAPERSIZE_A3;ws.page_setup.fitToWidth=1;ws.page_setup.fitToHeight=1
 ws.print_options.horizontalCentered=True;ws.page_margins.left=.25;ws.page_margins.right=.25;ws.page_margins.top=.3;ws.page_margins.bottom=.3
 ws.oddFooter.center.text='Team StratWise | VOLT-FORGE | 1 November 2026 | A'+str(index+1)
 return ws

def band(ws,r,s):return text(ws,r,s,bold=True,color=WHITE,fill=BLUE,height=25)

def table(ws,r,headers,rows,widths=None):
 n=len(headers);edges=widths or [(i*12//n+1,(i+1)*12//n) for i in range(n)]
 for j,h in enumerate(headers):text(ws,r,h,*edges[j],bold=True,size=10,color=WHITE,fill=BLUE,height=32)
 for i,row in enumerate(rows,r+1):
  for j,v in enumerate(row):
   c=text(ws,i,v,*edges[j],size=10,fill=LIGHT if (i-r)%2 else WHITE,height=32)
   if isinstance(v,(int,float)):c.number_format='0.00' if isinstance(v,float) else '0';c.alignment=Alignment(horizontal='center',vertical='center')
 return r+len(rows)+1

def formula(ws,r,col,s,fmt='0.00'):
 c=ws.cell(r,col,s);c.number_format=fmt;c.font=Font(name='Arial',size=11,color='000000',bold=True);c.alignment=Alignment(horizontal='center',vertical='center');return c

def design(n,opt='baseline'):return next(d for d in summary['designs'] if d['count']==n and d['option']==opt)

ws=sheet(0,'The trade-off is real; the candidate is conditional','Does reducing cell count serve the same declared job?','Same-end 4 / 3 / 2-cell variants; identical load, duration and starting conditions. The table separates nominal behaviour from the required sensitivity gate.')
rows=[]
for n in [4,3,2]:
 d=design(n);m=d['nominal'];rows.append([n,m['peak_cell_current_A'],m['peak_temperature_C'],m['min_voltage_V'],n*1206,n*70])
table(ws,7,['Cells','Peak cell A','Peak °C','Lowest V','Cell cost ₹','Cell mass g'],rows)
for r in range(8,11):formula(ws,r,9,f'=A{r}*1206','₹#,##0');formula(ws,r,11,f'=A{r}*70','0" g"')
for r in range(8,11):ws.cell(r,1).comment=Comment('Extracted nominal result. Formula inputs ₹1,206/cell and 70 g/cell from configs/parts_prices_v1.json and cell_catalogue_v2.json. Cells only, excludes copper/board/enclosure/assembly.','VOLT-FORGE')
source(ws,12,'Final rerun summary, nominal rows','reports/final_release_v1/study/summary.json')
band(ws,14,'What the change buys, and what it gives up')
table(ws,15,['Measure','4 → 2 result','Interpretation'],[
 ['Cell cost reduction','=1-I10/I8','Half the listed cell cost; a total build saving has not been calculated.'],
 ['Cell mass reduction','=1-K10/K8','Half the cells’ mass; no enclosure/board mass claim.'],
 ['Peak current change','=C10-C8','More current per cell; compare with operating limits and mismatch cases.'],
 ['Lowest voltage change','=G10-G8','Less margin above the 3.3 V mission floor.'],
 ['Temperature change','=E10-E8','A larger simulated rise; predictive temperature accuracy is unestablished.'],
 ],[(1,3),(4,6),(7,12)])
for r in (16,17):ws.cell(r,4).number_format='0%'
for r,unit in [(18,'A'),(19,'V'),(20,'°C')]:ws.cell(r,4).number_format='0.00'+chr(34)+' '+unit+chr(34)
text(ws,22,'Decision: carry two cells forward as the smallest candidate tested. Keep three or four when redundancy or larger margins matter.',bold=True,fill=LIGHT,height=40)
text(ws,24,'Method: coupled circuit solve → cell state update → irreversible/reversible heat → lumped temperature → updated cell parameters. Saved results retain the graph, settings and model/software identity.',height=43)
text(ws,26,'Scope: a single parallel cell group. No ageing, mechanical packaging, core-temperature prediction, physical board protection or hardware acceptance is established.',color=ORANGE,fill=AMBER,height=40)
source(ws,28,'Cost and cell geometry','configs/parts_prices_v1.json')
source(ws,29,'Model equations and assumptions','src/voltforge/studio/temperature_engine.py')
ws.print_area='A1:L30'

ws=sheet(1,'Two is the smallest tested candidate, not a universal answer','How was the sizing decision derived?','Qualification requires every required Pi case to pass. Stress runs and random sensitivity samples are reported separately and are not probabilities of success.')
band(ws,7,'1 | Convert the declared power scenario to the solver input')
table(ws,8,['Power W','Assumed efficiency','Assumed floor V','Fixed-current proxy A'],[[25,.9,3.3,'=A9/(D9*G9)']],[(1,3),(4,6),(7,9),(10,12)])
ws.cell(9,4).number_format='0%';ws.cell(9,10).number_format='0.000'
text(ws,11,'25 W is the Pi 5 recommended supply envelope, not measured Pi draw. The solver holds 8.418 A constant; a true constant-power converter is not represented by this study.',height=37)
source(ws,12,'Pi 5 official supply specification','https://www.raspberrypi.com/products/raspberry-pi-5/')
band(ws,14,'2 | Apply the frozen gate to all positions and required sensitivities')
rows=[]
for n in [1,2,3,4]:
 d=design(n);w=d['worst_required'];rows.append([n,f"{d['required_passed']}/{d['required_cases']}",w.get('highest_cell_current_A','Refused'),w.get('lowest_voltage_V','No run'),w.get('highest_temperature_C','No run'),'Qualifies' if d['qualifies'] else 'Refused'])
table(ws,15,['Cells','Required pass','Worst cell A','Lowest V','Worst °C','Gate result'],rows)
text(ws,21,'Gate: complete 600 s; serve requested current; stay inside cell operating limits and model coverage; ≥3.3 V; calculate thermal state and close the first-law check. A closed energy balance detects accounting errors, not model bias.',height=44)
band(ws,23,'3 | Compare the qualifying wiring choices, then state what could reverse the choice')
table(ws,24,['Two-cell routing','Nominal peak A','Worst required A','12 A stress cases'],[[o,design(2,o)['nominal']['peak_cell_current_A'],design(2,o)['worst_required']['highest_cell_current_A'],f"{design(2,o)['stress']['passed']}/{design(2,o)['stress']['cases']}"] for o in ['baseline','thicker','opposite','combined']],[(1,4),(5,7),(8,10),(11,12)])
text(ws,30,'The study recommends opposite-end outputs. The slide holds same-end routing fixed to isolate cell-count trade-offs. Opposite-end routing requires physical return wiring; board layout may prevent it.',fill=LIGHT,height=39)
text(ws,32,'Two cells have no spare. Losing one leaves the refused one-cell scenario. Three remaining as two is a simulated contingency, not a tested fault/isolation system.',color=ORANGE,fill=AMBER,height=37)
source(ws,34,'Frozen protocol, tiers, mismatch magnitudes and ranking rule','configs/round1_design_study_v2.json')
source(ws,35,'4,006 final rerun cases and outcomes','reports/final_release_v1/study/cases.jsonl');ws.print_area='A1:L36'

ws=sheet(2,'A traceable parameter set still has transfer limits','Where do the cell and thermal numbers come from?','The prototype combines published cell tables, literature heat capacity, a fixture-specific cooling estimate and declared geometry. These have different evidential status.')
rows=[
 ['Electrical response','PyECN LG M50T, 3 RC branches; 32 charge knots × 5 temperatures.','Published import','4–100% charge; 15–55 °C. Same cell type does not establish batch accuracy.'],
 ['Heat capacity','58.5 J/K from Steinhardt et al., Table A.14.','Published reference','Held constant; source describes a different thermal observation/setup.'],
 ['Heat loss to room','0.15249 W/K from test 53 rest steps 4 and 6.','Fixture calibration','A used four-cell rig. Transfer to a different cell assembly is assumed.'],
 ['Cell size / mass','21.44 mm diameter × 70.8 mm height; maximum 70 g.','Draft manufacturer spec','Cell envelope only; no assembled pack layout, clearance or safety analysis.'],
 ['Links / converter','Copper dimensions/contact resistance; 90% backup efficiency.','Declared assumptions','Not measured on the recommended build. Advertised board 95% is input step-down.'],
 ['Low-charge regularization','Third-branch time constant held at 350.142 s below 18% charge.','Project modification','Unvalidated regularization, not an original measured value.'],
]
table(ws,7,['Input','Value / derivation','Status','Consequence'],rows,[(1,2),(3,6),(7,8),(9,12)])
for r in range(8,14):ws.row_dimensions[r].height=56
source(ws,15,'Exact catalogue, parameter provenance and limitations','configs/cell_catalogue_v2.json')
source(ws,16,'PyECN pinned source commit 32540fe','https://github.com/ImperialCollegeLondon/PyECN/tree/32540fe0819bfc4d099bcd601d1ab0625cb524a3')
source(ws,17,'Heat capacity, DOI 10.1016/j.est.2021.103065','https://doi.org/10.1016/j.est.2021.103065')
band(ws,19,'Dataset breadth and actual comparison coverage are different numbers')
table(ws,20,['Layer','Count / use','What it establishes'],[
 ['Published module dataset','54 experiments; 194 files checksum-verified','File identity/integrity; not 54 model validation tests.'],
 ['Module comparison subset','2 recorded discharges: test 28 and test 53','Test 28 uses the same rig; test 53 also informed cooling. Neither is a blind independent holdout.'],
 ['Adjacent-cell comparison','3 LG M50 cells × 2 currents = 6 discharges','Unrelated source and fixture; the M50 family is not confirmed identical to M50T.'],
 ['Closed records','Reserved records remain closed','Not counted as validation. No outcomes decoded for this release.'],
 ],[(1,3),(4,7),(8,12)])
for r in range(21,25):ws.row_dimensions[r].height=43
text(ws,26,'So what: traceability lets a reviewer reconstruct the model. Independent predictive accuracy and transfer to a new board/fixture remain open questions.',bold=True,fill=LIGHT,height=38)
source(ws,28,'Module dataset: Piombo et al., CC BY 4.0','https://doi.org/10.17632/zh58byr53c.2')
source(ws,29,'Adjacent LG M50 dataset: Chen et al., CC BY 4.0','https://doi.org/10.5281/zenodo.4032561')
source(ws,30,'Comparison allocation, independence and exclusions','configs/measured_comparison_v1.json');ws.print_area='A1:L31'

ws=sheet(3,'Software checks pass; predictive accuracy remains unestablished','What did the checks actually show?','Numerical consistency, repeatability and agreement with measurements answer different questions. A model can balance its energy perfectly and still predict a real cell poorly.')
table(ws,7,['Check','Observed result','What follows'],[
 ['Independent numerical reference','15/15 synthetic electrical and heat cases against PyBaMM','Historical implementation comparison; no experimental temperature accuracy claim.'],
 ['Frozen-study rerun',f"4,006/4,006 reproduced; {len(verify['study_differences'])} differing stored fields",'27,832 numeric values unchanged on the final engine.'],
 ['Energy accounting','3,964 calculated cases close; 42 cases refused','Internal accounting check; does not detect wrong material/model parameters.'],
 ['Automated regression','515 Python pass, 8 known skips; 74 JavaScript pass','Software regressions covered; physical performance and provider reasoning need separate checks.'],
 ],[(1,3),(4,7),(8,12)])
for r in range(8,12):ws.row_dimensions[r].height=40
band(ws,13,'Published-data comparison: all 8 base discharges miss both predeclared bands')
base=[x for x in measured if x.get('sensitivity') is None]
rows=[]
for x in base:
 label=x['case'].replace('test28_exact_m50t_module','Module test 28').replace('test53_used_fixture','Module test 53').replace('warwick_lg_m50_single_cell__LGM50_','M50 ')
 rows.append([label,x['voltage_rmse_V'],x['voltage_max_abs_V'],x['peak_rise_measured_K'],x['peak_rise_simulated_K'],'Miss / Miss'])
table(ws,14,['Discharge','V RMSE','V max error','Measured rise K','Model rise K','Voltage / temp'],rows,[(1,4),(5,5),(6,6),(7,8),(9,10),(11,12)])
text(ws,24,'Bands fixed before comparison: voltage RMSE ≤0.05 V AND max error ≤0.15 V; thermal |peak-rise error| ≤ max(1 K, 25% of measured rise). Four module sensitivity reruns also miss both: 0/12 comparison cases inside both bands.',height=43)
band(ws,26,'Current sharing: show the simple baseline beside the model')
rows=[]
for x,b in zip(engineering['current_sharing'],engineering['post_hoc']['share_detail']):rows.append([x['record'].split('_')[0],x['mean_absolute_share_error_points'],b['equal_share_error_points'],x['busiest_cell_match_fraction'],'Miss'])
table(ws,27,['Record','Model mean error pp','Equal-share error pp','Busiest-cell match','Frozen gate'],rows,[(1,2),(3,5),(6,8),(9,10),(11,12)])
for r in [28,29]:ws.cell(r,9).number_format='0%'
text(ws,31,'The selected early-discharge “34% versus 34%” slice is post hoc and is not a passed check. Sensor channel offsets and Hall-sum/cycler disagreement remain unresolved.',color=ORANGE,fill=AMBER,height=38)
source(ws,33,'Frozen measurement bands and method','configs/measured_comparison_v1.json')
source(ws,34,'Every comparison result, including sensitivities','reports/measured_comparison_v1/final/result.json')
source(ws,35,'Current sharing, equal-share baseline and post-hoc labels','reports/engineering_checks_v1/result.json')
source(ws,36,'Final verification receipt','reports/final_release_v1/verification.json');ws.print_area='A1:L37'

ws=sheet(4,'Sensitivity tests locate weak points; they are not confidence bands','Which assumptions move the candidate, and what remains untested?','Two-cell same-end Pi scenario. Change one declared input at a time. The frozen study also tests cell mismatch in every position and combinations separately.')
subset=[x for x in cases if x['count']==2 and x['option']=='baseline' and x['mission']=='pi' and (x['tier']=='nominal' or (x['tier']=='shared_sensitivity' and x['label'] in ['cooling_half','thermal_pair_half','heat_capacity_low','contact_double','room_plus_2','all_charge_minus_2']) or x['tier']=='converter_efficiency')]
rows=[[x['label'],x['peak_cell_current_A'],x['peak_temperature_C'],x['min_voltage_V'],'Pass' if x['passed'] else 'Miss'] for x in subset]
table(ws,7,['Declared scenario','Peak cell A','Peak °C','Lowest V','Required result'],rows,[(1,4),(5,6),(7,8),(9,10),(11,12)])
source(ws,18,'Scenario values are not probability distributions','configs/round1_design_study_v2.json')
band(ws,20,'Challenges outside the required gate')
table(ws,21,['Challenge','Observed / unresolved','Decision consequence'],[
 ['Higher current: 12 A stress','Same-end 2-cell: 30/31 deterministic stress cases; 59/62 combined samples. Opposite-end: 31/31 and 60/62.','Stress is report-only. Passing the Pi gate does not mean all loads or weak-cell combinations pass.'],
 ['Lower real Pi demand','The 25 W scenario uses a recommended supply envelope, not a measured draw.','Measure actual demand later; a smaller load can change the minimum cell count.'],
 ['Lost cell / open contact','One-cell scenario is refused. Three cells leaving two can serve the simulated scenario.','Two-cell choice has no spare; real fault currents, isolation and topology are unassessed.'],
 ['Board integration and safety','Battery overcurrent, backup efficiency, charge sharing and sensing remain unverified. X1205 v1.1 cutoff is 2.4 V.','A candidate board does not implement the declared 3.3 V mission floor or prove cell protection.'],
 ['Temperature forecast error','Published comparisons miss. Scaling exercises are scenarios, not statistical bounds.','No safety certification, confidence interval or guaranteed real maximum temperature.'],
 ],[(1,3),(4,8),(9,12)])
for r in range(22,27):ws.row_dimensions[r].height=55
text(ws,28,'Next evidence that changes the decision: actual Pi/board demand and efficiency; correct sensing and charge/discharge protection; independently measured voltage and temperature for the chosen arrangement. These are future physical checks, not a Round 1 claim.',bold=True,fill=LIGHT,height=46)
source(ws,30,'Detailed study and routing trade-offs','reports/final_release_v1/study/summary.json')
source(ws,31,'Board screening, topology and operating-limit conditions','src/voltforge/studio/parts.py');ws.print_area='A1:L32'

ws=sheet(5,'₹5 lakh is a price hypothesis; revenue does not yet justify the build','What would the proposed pricing need to earn?','Blue numbers are editable assumptions. Black cells calculate. Student counts describe an audience; only paid labs and teams generate revenue. No customer has tested these prices.')
# Compact working model. All derived quantities are live formulas.
table(ws,7,['Driver','Input','Meaning'],[
 ['Eligible specialised E&T colleges',2610,'AISHE 2021–22 responding-college subset; not all engineering institutions.'],
 ['Assumed adoption',.05,'Planning scenario, not a demand forecast.'],
 ['Lab price ₹ / year',50000,'Proposed annual licence. Students free.'],
 ['Team price ₹ / year',500000,'Agreed planning price, up to 5 seats; not tested with customers.'],
 ['Planning horizon years',5,'Customers assumed present from year one in recovery illustration.'],
 ],[(1,4),(5,6),(7,12)])
for r in range(8,13):ws.cell(r,5).font=Font(name='Arial',size=11,color='0000FF',bold=True)
ws.cell(9,5).number_format='0%'
text(ws,14,'At 5% reach: labs',1,3,bold=True);formula(ws,14,4,'=ROUNDDOWN(E8*E9,0)','0');text(ws,14,'Annual lab revenue ₹',6,9,bold=True);formula(ws,14,10,'=D14*E10','₹#,##0')
band(ws,16,'Reconstruct the build estimate before discussing recovery (₹ crore)')
rows=[]
for item in cost['work_breakdown_person_years']:
 py=sum(item.get(k,0) for k in cost['rates_lakh_per_year']);raw=sum(item.get(k,0)*cost['rates_lakh_per_year'][k]['value'] for k in cost['rates_lakh_per_year'])
 rows.append([item['name'],py,raw*cost['overhead_multiplier']['value']/100])
table(ws,17,['Workstream','Person-years','Loaded people ₹ cr'],rows,[(1,7),(8,9),(10,12)])
text(ws,29,'People subtotal',1,7,bold=True);formula(ws,29,10,'=SUM(J18:J27)')
text(ws,30,'Lab capital; 3-year recurring; one-off',1,7);ws.cell(30,8,1.0223);ws.cell(30,9,3);ws.cell(30,10,.5)
text(ws,31,'Contingency',1,7);ws.cell(31,8,.2);ws.cell(31,8).number_format='0%';formula(ws,31,10,'=(J29+SUM(H30:J30))*H31')
text(ws,32,'Full future-suite estimate ₹ cr',1,7,bold=True,fill=LIGHT);formula(ws,32,10,'=J29+SUM(H30:J30)+J31')
# Stage one: dataset/results/quality; all lab capex and lab operating costs.
text(ws,34,'Stage 1: dataset + results + quality; full lab costs',1,8,bold=True)
formula(ws,34,10,'=((J18+J23+J26)+H30+0.9+(I30-0.9+J30)*(J18+J23+J26)/J29)*(1+H31)')
text(ws,35,'Annual gross revenue to recover stage 1 over 5 years ₹ cr',1,8);formula(ws,35,10,'=J34/E12')
text(ws,36,'Teams needed after assumed lab revenue (before running costs)',1,8);formula(ws,36,10,'=ROUNDUP(MAX(0,J34*10000000/E12-J14)/E11,0)','0')
text(ws,38,'Annual revenue sensitivity (₹ crore): teams at ₹5 lakh plus labs at ₹50,000',bold=True,fill=LIGHT,height=29)
# Columns D / G / J; independent levers and formulas remain visible.
table(ws,39,['Lab adoption','0 teams','10 teams','25 teams','50 teams'],[[a, f'=ROUNDDOWN($E$8*A{r},0)*$E$10/10000000',f'=(ROUNDDOWN($E$8*A{r},0)*$E$10+10*$E$11)/10000000',f'=(ROUNDDOWN($E$8*A{r},0)*$E$10+25*$E$11)/10000000',f'=(ROUNDDOWN($E$8*A{r},0)*$E$10+50*$E$11)/10000000'] for r,a in enumerate([.01,.03,.05],40)],[(1,2),(3,4),(5,6),(7,9),(10,12)])
for r in range(40,43):ws.cell(r,1).number_format='0%'
ws.conditional_formatting.add('C40:L42',ColorScaleRule(start_type='min',start_color='F9E5DA',end_type='max',end_color='AED2D5'))
text(ws,44,'Caution: gross recovery excludes post-build running, support, sales, tax, churn and ramp-up. The team market is unsized. Stage boundaries are planning allocations, not a funded execution plan. ₹35.38 cr is the future suite, not the existing prototype.',color=ORANGE,fill=AMBER,height=44)
text(ws,46,'Cost basis: assumed staffing × proxy salary rates × 1.4 overhead, plus equipment/recurring costs and 20% contingency. Principal/physics rates are imperfect role proxies; effort, equipment and duration are unquoted estimates.',height=37)
source(ws,48,'All staffing quantities, proxy rate sources and cost assumptions','configs/build_cost_v1.json')
source(ws,49,'AISHE audience counts, college denominator and adoption caveats','configs/market_sizing_v1.json')
source(ws,50,'Commercial assumptions and stage allocation rule','configs/business_case_v1.json');ws.print_area='A1:L51'
# Expandable calculation detail, outside the exhibit's print area.
ws=wb['A6 Economics']
roles=list(cost['rates_lakh_per_year'])
for col,role in enumerate(roles,2):
 ws.cell(54,col,role);ws.cell(55,col,cost['rates_lakh_per_year'][role]['value']);ws.cell(55,col).comment=Comment(cost['rates_lakh_per_year'][role]['source']+'; '+cost['rates_lakh_per_year'][role].get('url',''),'VOLT-FORGE')
ws.cell(56,1,'Overhead factor');ws.cell(56,2,cost['overhead_multiplier']['value'])
ws.cell(57,1,'Duration years');ws.cell(57,2,cost['duration_years'])
for i,item in enumerate(cost['work_breakdown_person_years'],61):
 ws.cell(i,1,item['id'])
 for col,role in enumerate(roles,2):ws.cell(i,col,item.get(role,0))
 ws.cell(i-43,8,f'=SUM(B{i}:F{i})');ws.cell(i-43,10,f'=SUMPRODUCT(B{i}:F{i},$B$55:$F$55)*$B$56/100')
for i,item in enumerate(cost['lab'],73):
 ws.cell(i,1,item['item']);ws.cell(i,7,item['quantity']);ws.cell(i,8,item.get('unit_inr',item.get('unit_usd',0)*cost['usd_inr']['value']));ws.cell(i,10,f'=G{i}*H{i}')
ws.cell(30,8,'=SUM(J73:J77)/10000000')
for col,item in enumerate(cost['recurring_lakh_per_year'],2):ws.cell(80,col,item['value'])
ws.cell(30,9,'=SUM(B80:D80)*B57/100')
ws.cell(81,2,sum(x['value'] for x in cost['one_off_lakh']));ws.cell(30,10,'=B81/100')
for r in range(54,83):ws.row_dimensions[r].hidden=True;ws.row_dimensions[r].outlineLevel=1
ws.sheet_properties.outlinePr.summaryBelow=False

# Every hardcoded numeric source is adjacent, with additional comments for auditability.
for ws in wb:
 for row in ws:
  for c in row:
   if isinstance(c.value,(int,float)) and not c.comment:c.comment=Comment('Source: linked exhibit sources below. Extracted simulation/measurement values are observations from those reports; editable commercial values are labelled assumptions.','VOLT-FORGE')
   if c.data_type=='f':c.number_format=c.number_format if c.number_format!='General' else '0.00'
# Two visual tests of the argument, using the same visible source cells.
for sheet_name,anchor,title,columns,start,end in [
 ('A1 Decision','A32','Fewer cells increase peak current (A)',[3],8,10),
 ('A4 Accuracy','A39','Measured versus modelled peak rise (K)',[7,9],15,22),
]:
 ws=wb[sheet_name];chart=BarChart();chart.type='col';chart.title=title;chart.style=10;chart.width=24;chart.height=8
 for col in columns:chart.add_data(Reference(ws,min_col=col,min_row=start-1,max_row=end),titles_from_data=True)
 chart.set_categories(Reference(ws,min_col=1,min_row=start,max_row=end));chart.y_axis.title='A' if sheet_name=='A1 Decision' else 'Temperature rise (K)'
 if sheet_name=='A1 Decision':chart.legend=None
 ws.add_chart(chart,anchor);ws.print_area='A1:L49' if sheet_name=='A1 Decision' else 'A1:L56'
wb.active=0;OUT.parent.mkdir(parents=True,exist_ok=True);wb.save(OUT);print(OUT)
