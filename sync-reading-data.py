"""Publish only validated, de-identified browser task summaries.

Input must come from a COMPLETE, successful read of every ongoing task-list page.
This program does not log in, read browser credentials, or call private APIs.
"""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ALLOWED = {'name', 'publishedAt', 'dates', 'days', 'rate', 'completion', 'verified',
           'verifiedCount', 'zeroCount', 'partialCount', 'detailUpdatedAt'}
TZ = timezone(timedelta(hours=8))

def validate(payload):
    if payload.get('complete') is not True or payload.get('source') != 'school.lingshi.com':
        raise ValueError('A complete successful platform read is required')
    if not isinstance(payload.get('tasks'), list):
        raise ValueError('Missing task list')
    observed = datetime.fromisoformat(payload['observedAt'])
    if observed.tzinfo is None:
        raise ValueError('Observation time must include timezone')
    if abs((datetime.now(TZ) - observed).total_seconds()) > 7200:
        raise ValueError('Observation is too old or in the future')
    tasks, seen = [], set()
    for item in payload['tasks']:
        if set(item) - ALLOWED:
            raise ValueError('Unknown fields: do not submit student identities or accounts')
        for key in ('name', 'publishedAt', 'dates', 'days', 'rate', 'completion'):
            if not isinstance(item.get(key), str):
                raise ValueError('Missing task field: ' + key)
        if re.search(r'\b1[3-9]\d{9}\b', item['name']):
            raise ValueError('Possible personal identifier in task name')
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}至\d{4}-\d{2}-\d{2}', item['dates']):
            raise ValueError('Invalid task date range')
        start, end = [datetime.strptime(v, '%Y-%m-%d').date() for v in item['dates'].split('至')]
        if not start <= observed.astimezone(TZ).date() <= end:
            raise ValueError('Only currently ongoing tasks are accepted')
        if not re.fullmatch(r'\d+/\d+', item['days']):
            raise ValueError('Invalid task day count')
        for key in ('rate', 'completion'):
            if not re.fullmatch(r'\d+(\.\d+)?%', item[key]) or not 0 <= float(item[key][:-1]) <= 100:
                raise ValueError('Invalid percentage')
        identity = '\n'.join(item[k] for k in ('name', 'publishedAt', 'dates'))
        key = 'R' + hashlib.sha256(identity.encode()).hexdigest()[:10]
        if key in seen:
            raise ValueError('Duplicate task identity')
        seen.add(key)
        t = {k: item[k] for k in ('name', 'publishedAt', 'dates', 'days', 'rate', 'completion')}
        t.update(id=key, verified=False, verifiedCount=None, zeroCount=None, partialCount=None,
                 newToday=start == observed.astimezone(TZ).date())
        if item.get('verified') is True:
            if item.get('detailUpdatedAt') != payload['observedAt']:
                raise ValueError('Detail aggregates must be verified during the current read')
            for k in ('verifiedCount', 'zeroCount', 'partialCount'):
                if type(item.get(k)) is not int or item[k] < 0:
                    raise ValueError('Invalid verified aggregate')
            if item['zeroCount'] > item['verifiedCount'] or item['partialCount'] > item['verifiedCount']:
                raise ValueError('Aggregate exceeds verified records')
            t.update({k: item[k] for k in ('verifiedCount', 'zeroCount', 'partialCount')})
            t.update(verified=True, detailUpdatedAt=payload['observedAt'])
        tasks.append(t)
    return {'updated': observed.astimezone(TZ).date().isoformat(), 'updatedAt':payload['observedAt'],
            'source':'学员平台任务情况及本次核实的详情',
            'verifiedRecords':sum(t['verifiedCount'] or 0 for t in tasks), 'tasks':tasks}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('input',type=Path)
    parser.add_argument('--validate-only',action='store_true')
    args=parser.parse_args()
    data=validate(json.loads(args.input.read_text(encoding='utf-8-sig')))
    if not args.validate_only:
        target=ROOT/'reading-tasks.json'
        temp=target.with_suffix('.json.tmp')
        temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        temp.replace(target)
    print(json.dumps({'validated':True,'tasks':len(data['tasks']),'verifiedRecords':data['verifiedRecords'],
                      'updatedAt':data['updatedAt']},ensure_ascii=False))

if __name__=='__main__': main()
