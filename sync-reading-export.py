"""Convert a newly downloaded task export to a safe public task snapshot."""
import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import openpyxl

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('reading_sync',ROOT/'sync-reading-data.py')
sync=importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)

def convert(path):
    now=datetime.now(timezone(timedelta(hours=8)))
    age=now.timestamp()-path.stat().st_mtime
    if age < -60 or age > 7200:
        raise ValueError('Export is not recent; download a fresh task export from the platform')
    ws=openpyxl.load_workbook(path,read_only=True,data_only=True).active
    values=list(ws.values)
    required=['任务名称','发布时间','起止日期','任务状态','已进行/总天数','打卡率','完成度']
    if not values or not all(k in values[0] for k in required):
        raise ValueError('Not a complete task export with the required fields')
    rows=[dict(zip(values[0],r)) for r in values[1:] if any(v is not None for v in r)]
    if not rows:
        raise ValueError('An empty export cannot establish that all tasks have ended')
    tasks=[]
    for row in rows:
        if row['任务状态']!='进行中': continue
        tasks.append({k:str(row[src]).strip() for k,src in {
          'name':'任务名称','publishedAt':'发布时间','dates':'起止日期',
          'days':'已进行/总天数','rate':'打卡率','completion':'完成度'}.items()})
    observed=datetime.fromtimestamp(path.stat().st_mtime,timezone(timedelta(hours=8)))
    return {'complete':True,'source':'school.lingshi.com','observedAt':observed.isoformat(timespec='seconds'),'tasks':tasks}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('export',type=Path)
    parser.add_argument('--validate-only',action='store_true')
    args=parser.parse_args()
    data=sync.validate(convert(args.export))
    if not args.validate_only:
        target=ROOT/'reading-tasks.json'
        temp=target.with_suffix('.json.tmp')
        temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        temp.replace(target)
    print(json.dumps({'tasks':len(data['tasks']),'updatedAt':data['updatedAt'],'containsStudentIdentifiers':False},ensure_ascii=False))

if __name__=='__main__': main()
