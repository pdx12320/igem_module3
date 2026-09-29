import fs from 'node:fs/promises';
import path from 'node:path';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const root = process.argv[2] || '/workspace/scratch/c18fccb23287/skill_clustering';
const temp = '/tmp/cp_pipeline_workbook_c18fccb23287';
const data = JSON.parse(await fs.readFile(path.join(temp,'workbook_data.json'),'utf8'));
const qa = path.join(temp,'qa');
await fs.mkdir(qa,{recursive:true});
const wb = Workbook.create();
const font='Noto Sans CJK SC';
const color={ink:'#213447',head:'#314F67',muted:'#5E6E7A',band:'#F2F5F7',line:'#9DB1BF',warn:'#FFF0CF',warnInk:'#865314'};
const col = n => {let s='';while(n){n--;s=String.fromCharCode(65+n%26)+s;n=Math.floor(n/26);}return s;};
function setup(name,title,note,widths,rows=45){
  const sh=wb.worksheets.add(name); sh.showGridLines=false;
  sh.tabColor=name==='方法说明'?'#8496A3':'#314F67';
  const end=col(widths.length+1);
  sh.getRange(`A1:${end}${rows}`).format={font:{name:font,size:10,color:color.ink},rowHeightPx:27,verticalAlignment:'center'};
  sh.getRange(`A1:A${rows}`).format.columnWidthPx=17;
  widths.forEach((w,i)=>sh.getRange(`${col(i+2)}1:${col(i+2)}${rows}`).format.columnWidthPx=w);
  sh.getRange('B2').values=[[title]];
  sh.getRange('B2').format.font={name:font,size:15,bold:true,color:color.ink};
  sh.getRange(`B2:${end}2`).format.rowHeightPx=35;
  sh.getRange(`B3:${end}3`).format.borders={bottom:{style:'thin',color:color.line}};
  sh.getRange('B4').values=[[note]];
  sh.getRange('B4').format.font={name:font,size:10,color:color.muted};
  sh.getRange('B4').format.wrapText=false;
  return sh;
}
function table(sh,name,headers,rows,{start=6,widths=[],numeric=[],formats={},wrap=[],height=32}={}){
  const endRow=start+rows.length, end=col(headers.length+1);
  const range=sh.getRange(`B${start}:${end}${endRow}`);
  range.values=[headers,...rows];
  range.format={font:{name:font,size:10,color:color.ink},rowHeightPx:height,verticalAlignment:'center',wrapText:false};
  const t=sh.tables.add(`B${start}:${end}${endRow}`,true,name);t.style='TableStyleLight1';t.showFilterButton=true;
  for(let r=start+1;r<=endRow;r++)sh.getRange(`B${r}:${end}${r}`).format.fill=(r-start)%2?color.band:'#FFFFFF';
  const head=sh.getRange(`B${start}:${end}${start}`);
  head.format={fill:color.head,font:{name:font,size:10,color:'#FFFFFF',bold:true},horizontalAlignment:'center',verticalAlignment:'center',rowHeightPx:55,wrapText:true,borders:{insideVertical:{style:'thin',color:'#FFFFFF'}}};
  for(let i=0;i<headers.length;i++){
    const b=sh.getRange(`${col(i+2)}${start+1}:${col(i+2)}${endRow}`);
    b.format.horizontalAlignment=numeric.includes(i)?'right':'left';
    if(formats[i])b.setNumberFormat(formats[i]);
    if(wrap.includes(i))b.format.wrapText=true;
  }
  sh.freezePanes.freezeRows(start);
  sh.freezePanes.freezeColumns(2);
}

const flowHeaders=['流程标识','CP 特征','算法','用途','特征数','选定 k','非噪声簇数','噪声构建数','覆盖率','单构建簇数','原始全 CP 轮廓系数','拟合空间轮廓系数','重选 k 完全重复率','固定 k 完全重复率','重选 k 平均 ARI','固定 k 平均 ARI','各簇人数','PCA 维数','PCA 保留方差','解释限制'];
const flow=setup('流程比较','32 条 CP 聚类流程比较','200 次 seed 重采样。跨流程优先比较原始全 CP 指标，并同时查看覆盖率与单构建簇。',[280,156,160,86,75,70,95,96,86,100,120,120,120,120,115,115,112,86,110,390]);
table(flow,'PipelineComparison',flowHeaders,data.pipeline_rows,{numeric:[4,5,6,7,8,9,10,11,12,13,14,15,17,18],formats:{4:'0',5:'0',6:'0',7:'0',8:'0.0%',9:'0',10:'0.000',11:'0.000',12:'0.0%',13:'0.0%',14:'0.000',15:'0.000',17:'0',18:'0.0%'}});
flow.getRange('I7:I38').conditionalFormats.add('cellIs',{operator:'greaterThan',formula:0,format:{fill:color.warn,font:{color:color.warnInk}}});
flow.getRange('U7:U38').conditionalFormats.add('containsText',{text:'全部为噪声',format:{fill:color.warn,font:{color:color.warnInk,bold:true}}});

const constructHeaders=['提交构建名','结构实际突变','原表活性','活性对照状态','已到 seed','全 CP Ward','全 CP 平均连接','全 CP 完全连接','全 CP K-means','全 CP PCA95 + K-means','全 CP 谱聚类','PCA3 + GMM','HDBSCAN min=2','HDBSCAN min=3','DBSCAN q50','DBSCAN q75','前 10% 谱聚类','高置信 CP Ward','70–153 核心 Ward','说明'];
const con=setup('构建对照','11 个构建与原始活性对照','簇编号从 0 开始，仅在各流程内部有效。−1 为噪声。活性保持原表刻度，空白保持缺失。',[180,220,86,125,90,...Array(14).fill(112),590],21);
table(con,'ConstructComparison',constructHeaders,data.construct_rows,{numeric:[2,4,...Array.from({length:14},(_,i)=>i+5)],formats:{2:'0.000'},height:34});
con.getRange('E7:E17').conditionalFormats.add('containsText',{text:'缺失',format:{fill:color.warn,font:{color:color.warnInk}}});
con.getRange('E7:E17').conditionalFormats.add('containsText',{text:'不符',format:{fill:color.warn,font:{color:color.warnInk,bold:true}}});
con.getRange('G7:T17').conditionalFormats.add('cellIs',{operator:'equal',formula:-1,format:{fill:'#E9EDF0',font:{color:'#6D7882'}}});

const candidateHeaders=['残基','原方差排名','唯一分区 BCSS 等权排名','3 种分区中前 20 占比','去构建方差最佳排名','去构建方差最差排名','11 次去构建方差前 20 占比','主要差异接触','序列来源','催化注释','最低构建 pLDDT','存在 pLDDT <70','本轮解释'];
const cand=setup('候选一致性','17 个既有候选的跨流程一致性','6 个主算法产生 3 种唯一分区，按唯一分区等权。去构建分析评估现有突变面板敏感性。',[80,100,115,125,105,105,140,145,170,185,125,120,550],29);
const candNumeric=data.candidate_keys.map((k,i)=>data.candidate_numeric_keys.includes(k)?i:-1).filter(i=>i>=0);
const rows=data.candidate_rows.map(r=>r.map((v,i)=>i===11?(v==='True'?'是':'否'):v));
table(cand,'CandidateConsensus',candidateHeaders,rows,{numeric:candNumeric,formats:{1:'0',2:'0',3:'0.0%',4:'0',5:'0',6:'0.0%',10:'0.0'},height:34});
cand.getRange('M7:M23').conditionalFormats.add('containsText',{text:'是',format:{fill:color.warn,font:{color:color.warnInk}}});

const method=setup('方法说明','流程参数、指标与来源','活性仅用于聚类完成后的对照，未参与模型拟合与选择。计算稳健性与实验活性证据分别解释。',[210,1000],42);
table(method,'MethodDefinitions',['项目','定义或来源'],data.method_rows,{height:40,wrap:[1]});
method.freezePanes.unfreeze();

wb.recalculate();
const inspect=[];
for(const [name,range] of [['流程比较','B6:Q12'],['构建对照','B6:G17'],['候选一致性','B6:H23'],['方法说明','B6:C13']]){
  inspect.push((await wb.inspect({kind:'table',range:`${name}!${range}`,include:'values,formulas',tableMaxRows:18,tableMaxCols:16,maxChars:3500})).ndjson);
}
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:25},maxChars:1200});
await fs.writeFile(path.join(qa,'inspection.ndjson'),inspect.join('\n')+'\n'+errors.ndjson);
const renders=[['流程比较','A1:L15','flow_left'],['流程比较','M6:U15','flow_right'],['流程比较','B30:U38','flow_density_core'],['构建对照','A1:L17','construct_left'],['构建对照','M6:U17','construct_right'],['候选一致性','A1:I23','candidate_left'],['候选一致性','J6:N23','candidate_right'],['方法说明','A1:C20','methods_top'],['方法说明','B21:C36','methods_bottom']];
const renderOnly=process.env.CP_RENDER_ONLY?JSON.parse(process.env.CP_RENDER_ONLY):null;
for(const [sheetName,range,name] of renders){
  if(renderOnly&&!renderOnly.includes(name)) continue;
  const blob=await wb.render({sheetName,range,scale:1.2,format:'png'});
  await fs.writeFile(path.join(qa,name+'.png'),new Uint8Array(await blob.arrayBuffer()));
}
const out=path.join(root,'deliverables/CP_clustering_workflow_comparison.xlsx');
await fs.mkdir(path.dirname(out),{recursive:true});
await (await SpreadsheetFile.exportXlsx(wb)).save(out);
console.log(JSON.stringify({output:out,qa,rows:[data.pipeline_rows.length,data.construct_rows.length,data.candidate_rows.length,data.method_rows.length],error_scan:errors.ndjson}));
