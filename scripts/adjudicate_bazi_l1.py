#!/usr/bin/env python3
import argparse, json
from datetime import date, datetime
from pathlib import Path

CLASH={frozenset(x) for x in [('子','午'),('丑','未'),('寅','申'),('卯','酉'),('辰','戌'),('巳','亥')]}
HARM={frozenset(x) for x in [('子','未'),('丑','午'),('寅','巳'),('卯','辰'),('申','亥'),('酉','戌')]}
SIX_COMBINE={frozenset(x) for x in [('子','丑'),('寅','亥'),('卯','戌'),('辰','酉'),('巳','申'),('午','未')]}
HALF_COMBINE={frozenset(x):element for x,element in [
    (('申','子'),'水'),(('子','辰'),'水'),(('亥','卯'),'木'),(('卯','未'),'木'),
    (('寅','午'),'火'),(('午','戌'),'火'),(('巳','酉'),'金'),(('酉','丑'),'金')]}
STEM_INFO={'甲':('木',1),'乙':('木',0),'丙':('火',1),'丁':('火',0),'戊':('土',1),'己':('土',0),'庚':('金',1),'辛':('金',0),'壬':('水',1),'癸':('水',0)}
GENERATES={'木':'火','火':'土','土':'金','金':'水','水':'木'}
CONTROLS={'木':'土','土':'水','水':'火','火':'金','金':'木'}
BRANCH_HIDDEN={
    '子':[('癸',1.0)], '丑':[('己',0.60),('癸',0.30),('辛',0.10)],
    '寅':[('甲',0.60),('丙',0.30),('戊',0.10)], '卯':[('乙',1.0)],
    '辰':[('戊',0.60),('乙',0.30),('癸',0.10)], '巳':[('丙',0.60),('戊',0.30),('庚',0.10)],
    '午':[('丁',0.70),('己',0.30)], '未':[('己',0.60),('丁',0.30),('乙',0.10)],
    '申':[('庚',0.60),('壬',0.30),('戊',0.10)], '酉':[('辛',1.0)],
    '戌':[('戊',0.60),('辛',0.30),('丁',0.10)], '亥':[('壬',0.70),('甲',0.30)],
}
SEASON_ELEMENT={'寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水','子':'水','丑':'土'}

def derive_strength_inputs(fp):
    """Build the auditable L1 contract when legacy L0 omitted its table expansion.

    This derives only deterministic seasonal, root, visible/hidden and candidate
    fields from the four pillars. It deliberately keeps formal structure and
    useful-element decisions conditional.
    """
    day_stem=fp.get('day',{}).get('stem')
    month_branch=fp.get('month',{}).get('branch')
    if day_stem not in STEM_INFO or month_branch not in BRANCH_HIDDEN:
        return {}
    day_element=STEM_INFO[day_stem][0]
    generating_element=next(element for element,target in GENERATES.items() if target==day_element)
    positions=('year','month','day','hour')
    roots=[]; hidden_support=0.0; hidden_opposition=0.0; census={x:0.0 for x in '木火土金水'}
    hidden_rows={}
    for position in positions:
        branch=fp.get(position,{}).get('branch')
        stems=BRANCH_HIDDEN.get(branch,[])
        hidden_rows[position]={'branch':branch,'stems':[{'stem':stem,'weight':weight,'ten_god':ten_god(day_stem,stem)} for stem,weight in stems]}
        for stem,weight in stems:
            element=STEM_INFO[stem][0]; census[element]+=weight
            if element==day_element:
                roots.append({'position':position,'branch':branch,'stem':stem,'weight':weight,'qi':'main' if weight>=0.6 else 'residual'})
                hidden_support+=weight
            elif element==generating_element:
                hidden_support+=weight*0.8
            else:
                hidden_opposition+=weight
    visible_support=0.0; visible_opposition=0.0
    visible=[]
    for position in positions:
        stem=fp.get(position,{}).get('stem')
        if stem not in STEM_INFO or position=='day': continue
        element=STEM_INFO[stem][0]; census[element]+=1.0
        item={'position':position,'stem':stem,'element':element,'ten_god':ten_god(day_stem,stem)}; visible.append(item)
        if element==day_element: visible_support+=1.0
        elif element==generating_element: visible_support+=0.8
        else: visible_opposition+=1.0
    gets_command=SEASON_ELEMENT.get(month_branch)==day_element
    seasonal_bonus=2.5 if gets_command else (1.2 if GENERATES.get(SEASON_ELEMENT.get(month_branch))==day_element else 0.0)
    support_score=seasonal_bonus+visible_support+hidden_support
    opposition_score=visible_opposition+hidden_opposition
    if gets_command and support_score>=opposition_score+1.5:
        classification='身旺有根'
    elif support_score>=opposition_score+0.5:
        classification='身偏旺有根'
    elif roots and (visible_support+hidden_support)>0:
        classification='身弱有根有助'
    else:
        classification='身弱少助'
    month_lord=BRANCH_HIDDEN[month_branch][0][0]
    month_tg=ten_god(day_stem,month_lord)
    structure_name=f'{month_tg}當令（條件式）'
    if month_tg in ('比肩','劫財'):
        supporting='月令與根氣提高日主自主性，需由財官食傷判斷如何疏導。'
        competing='比劫過旺可能分財或令選擇分散；是否成立須看歲運引動。'
    else:
        supporting='月令十神形成主要結構候選，需與透干、根氣及制化共同裁決。'
        competing='月令候選可能被更強的透干或合沖關係修正。'
    return {
        'day_master':day_stem,
        'month_command':{'branch':month_branch,'main_stem':month_lord,'ten_god':month_tg,'season_element':SEASON_ELEMENT.get(month_branch)},
        'day_master_roots':roots,
        'root_strength':{'root_count':len(roots),'weighted_root_score':round(sum(x['weight'] for x in roots),2),'roots':roots},
        'element_census':{k:round(v,2) for k,v in census.items()},
        'seasonal_strength':{'gets_command':gets_command,'season_element':SEASON_ELEMENT.get(month_branch),'seasonal_bonus':seasonal_bonus},
        'day_master_score':{'visible_support_excluding_day_master':round(visible_support,2),'hidden_support':round(hidden_support,2),'visible_opposition':round(visible_opposition,2),'hidden_opposition':round(hidden_opposition,2),'support_total':round(support_score,2),'opposition_total':round(opposition_score,2)},
        'day_master_classification':{'classification':classification,'reason':f'依月令、{len(roots)}個同元素藏干根、透干及藏干加權比較；支持{support_score:.2f}，異黨{opposition_score:.2f}。'},
        'structure_candidates':[{'name':structure_name,'supporting_mechanism':supporting,'competing_mechanism':competing}],
        'structure_failure_conditions':['若月令主氣、根氣或透干資料校驗改變，候選結構必須重算。','未完成制化與合化條件前不得升格為純格。'],
        'climate_adjustment':{'status':'conditional','season':SEASON_ELEMENT.get(month_branch),'note':'調候與結構分開；本模組不把候選元素寫成固定吉凶。'},
        'useful_god_candidates':{'status':'conditional','favorable':[],'unfavorable':[],'warning':'只完成強弱與結構候選；喜用須按具體作用鏈及歲運另判。'},
        'hidden_stems_with_weights':hidden_rows,
        'visible_stems':visible,
        'source':'derived_l1_contract_v1',
    }

def get_bazi(chart):
    node=chart.get('systems',{}).get('bazi',{})
    if node.get('status')!='ok': raise ValueError('bazi system is not validated')
    return node.get('data',{})

def contacts(a,b):
    pair=frozenset((a,b)); out=[]
    if pair in CLASH: out.append('clash')
    if pair in HARM: out.append('harm')
    if pair in SIX_COMBINE: out.append('six_combination')
    if pair in HALF_COMBINE: out.append('half_combination_'+HALF_COMBINE[pair])
    if pair==frozenset(('子','卯')): out.append('punishment')
    if a==b: out.append('repeat')
    return out

def ten_god(day_stem, other_stem):
    de,dy=STEM_INFO[day_stem]; oe,oy=STEM_INFO[other_stem]; same=dy==oy
    if oe==de: return '比肩' if same else '劫財'
    if GENERATES[oe]==de: return '偏印' if same else '正印'
    if GENERATES[de]==oe: return '食神' if same else '傷官'
    if CONTROLS[de]==oe: return '偏財' if same else '正財'
    if CONTROLS[oe]==de: return '七殺' if same else '正官'
    raise ValueError('unhandled ten-god relation')

def adjudicate(chart, as_of):
    b=get_bazi(chart)
    fp=b.get('four_pillars',{})
    enhanced=b.get('enhanced_v3_0_8',{})
    s=enhanced.get('strength_inputs_v1') or derive_strength_inputs(fp)
    required=['day_master','month_command','day_master_roots','root_strength','element_census','seasonal_strength','day_master_score','day_master_classification','structure_candidates','climate_adjustment','useful_god_candidates']
    missing=[x for x in required if x not in s]
    classification=s.get('day_master_classification',{}).get('classification')
    root=s.get('root_strength',{})
    score=s.get('day_master_score',{})
    support=float(score.get('visible_support_excluding_day_master',0))+float(score.get('hidden_support',0))
    expected='身弱有根有助' if (not s.get('seasonal_strength',{}).get('gets_command') and root.get('root_count',0)>0 and support>0) else None
    strength_verified=not missing and bool(classification) and (expected is None or classification==expected)
    follow_rejected=bool(root.get('root_count',0)>0 or support>0)

    candidates=s.get('structure_candidates',[])
    structure_value=candidates[0].get('name') if candidates else None
    structure_status='conditional_structure' if structure_value else 'insufficient'
    useful=s.get('useful_god_candidates',{})

    birth=datetime.fromisoformat(b.get('true_solar_time',{}).get('input_birth_dt') or chart.get('input',{}).get('birth_datetime')).date()
    age=as_of.year-birth.year-((as_of.month,as_of.day)<(birth.month,birth.day))
    current=None
    for lp in b.get('luck_pillars',[]):
        if lp.get('start_age',999)<=age<=lp.get('end_age',-1): current=lp
    natal_branches=[fp.get(x,{}).get('branch') for x in ('year','month','day','hour')]
    luck_contacts=[]
    if current:
        for idx,branch in enumerate(natal_branches):
            for kind in contacts(current.get('branch'),branch): luck_contacts.append({'type':kind,'natal_position':('year','month','day','hour')[idx],'natal_branch':branch,'luck_branch':current.get('branch')})

    annual=[]
    for row in b.get('annual_cycles',[]):
        year=row.get('year')
        if year not in range(2025,2031): continue
        stem=row.get('annual_pillar',{}).get('stem'); branch=row.get('annual_pillar',{}).get('branch')
        interactions=[]
        for idx,nb in enumerate(natal_branches):
            for kind in contacts(branch,nb): interactions.append({'type':kind,'with':('year','month','day','hour')[idx],'branch':nb})
        if current:
            for kind in contacts(branch,current.get('branch')): interactions.append({'type':kind,'with':'luck_pillar','branch':current.get('branch')})
        tg=row.get('annual_stem_ten_god','')
        supportive=tg in ('正印','偏印','比肩','劫財','劫财')
        pressure=tg in ('正財','偏財','正财','偏财','正官','七殺','七杀','食神','傷官','伤官')
        structural=any(x['type'] in ('clash','punishment') for x in interactions)
        mixed_relation=any(x['type'].startswith('half_combination_') or x['type']=='six_combination' for x in interactions)
        label='structural_change' if structural else ('mixed' if mixed_relation or (supportive and interactions) else 'supportive' if supportive else 'pressurising' if pressure else 'mixed')
        annual.append({'year':year,'pillar':stem+branch,'ten_god':tg,'net_label':label,'interactions':interactions,'boundary_note':'流年以立春切換；不是事件發生日'})

    evidence={
      'strength':['BA-L1-month-command','BA-L1-root','BA-L1-visible-hidden-support'],
      'structure':['BA-L1-structure-candidate','BA-L1-control-or-transformation','BA-L1-competing-chain'],
      'luck':['BA-L1-current-luck','BA-L1-luck-branch-contacts']}

    def bounded(position, reason, evidence_ids, limitation, failure_rule):
        return {'position':position,'reason':reason,'evidence_ids':evidence_ids,
                'limitation':limitation,'failure_rule':failure_rule}

    if not strength_verified:
        reason='八字L1缺少完成旺衰裁決所需欄位：' + ('、'.join(missing) if missing else '強弱分類未通過一致性檢查')
        positions={name:bounded('insufficient',reason,[], '不得輸出身強弱、格局、喜用或領域方向。','補齊並通過L1強弱與結構校驗後重新分析。')
                   for name in ('career','wealth','relationship','home_family','authority_status')}
    else:
        dm=s.get('day_master') or fp.get('day',{}).get('stem')
        month=s.get('month_command')
        luck_name=(current or {}).get('pillar') or ((current or {}).get('stem','')+(current or {}).get('branch','')) or '未提供'
        structure_text=structure_value or '未定格局'
        positions={
          'career':bounded('refine',f'日主{dm}的強弱裁決為「{classification}」，結構候選為「{structure_text}」；八字只修正承擔工作責任的方式。',evidence['strength']+evidence['structure'],'不能由格局候選直接指定行業、職位或升遷結果。','若職業表現與此結構候選所描述的責任方式長期無關，應下修。'),
          'wealth':bounded('refine',f'已驗證強弱為「{classification}」；財星能否轉化為可留存資源，仍須與承載和現行{luck_name}大運一起判斷。',evidence['strength']+evidence['luck'],'不能把財星出現直接翻譯成富有、破財或具體收入。','若收入、負擔與留存長期不隨相同條件變化，應下修。'),
          'relationship':bounded('not_comparable','八字本次只保留日支及歲運接觸，沒有足夠證據判定伴侶品質或婚姻結果。',['BA-L1-day-branch']+evidence['luck'],'不得指定婚期、對象性格或關係必然吉凶。','取得可驗證的配偶星、日支與歲運完整裁決後再比較。'),
          'home_family':bounded('refine',f'現行{luck_name}大運與本命地支共有{len(luck_contacts)}項可追蹤接觸，只能修正生活基地的變動壓力。',evidence['luck'],'不能由沖合刑害單獨推出搬屋、置業或家庭事件。','若對應期間沒有任何住處、固定支出或家庭責任變動，應下修。'),
          'authority_status':bounded('refine',f'強弱「{classification}」與「{structure_text}」候選共同描述權責的承擔條件。',evidence['strength']+evidence['structure'],'條件式格局不得寫成已完成，也不能保證地位。','若權責變化與該結構機制無關，應下修。')
        }

    return {
      'model_version':'bazi_l1_v1','status':'ok' if strength_verified else 'insufficient','input_engine_version':b.get('_version') or chart.get('systems',{}).get('bazi',{}).get('engine_version'),
      'input_audit':{'required_fields':required,'missing_fields':missing,'classification_expected_from_guardrail':expected,'classification_consistent':classification==expected if expected else True,'as_of':as_of.isoformat(),'age':age},
      'strength_decision':{'status':'verified' if strength_verified else 'insufficient','value':classification,'month_command':s.get('month_command'),'root_strength':root,'visible_hidden_support':support,'follow_structure_allowed':not follow_rejected,'reason':s.get('day_master_classification',{}).get('reason')},
      'structure_decision':{'status':structure_status if strength_verified else 'insufficient','value':structure_value if strength_verified else None,'supporting_mechanism':(candidates[0].get('supporting_mechanism') if candidates else None),'competing_mechanism':(candidates[0].get('competing_mechanism') if candidates else None),'failure_conditions':s.get('structure_failure_conditions',[])},
      'useful_element_decision':{'status':useful.get('status','insufficient'),'support_candidates':useful.get('favorable',[]),'unfavorable_candidates':useful.get('unfavorable',[]),'climate':s.get('climate_adjustment'),'warning':useful.get('warning')},
      'current_luck_pillar':current,'current_luck_contacts':luck_contacts,'annual_activation':annual,'domain_positions':positions,
      'reader_safe_summary':(f'八字L1已通過：日主{(s.get("day_master") or fp.get("day",{}).get("stem"))}，強弱裁決為「{classification}」，結構候選為「{structure_value or "未定"}」。所有領域結論仍須保留限制與反證。' if strength_verified else '八字四柱可以核對，但L1旺衰、格局與喜用尚未通過必要欄位及一致性校驗。本次不得輸出任何方向性八字結論。')
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('chart',type=Path); ap.add_argument('output',type=Path); ap.add_argument('--as-of',default=date.today().isoformat()); ap.add_argument('--strict',action='store_true',help='return non-zero when L1 is insufficient')
    a=ap.parse_args(); result=adjudicate(json.loads(a.chart.read_text(encoding='utf-8')),date.fromisoformat(a.as_of))
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':result['status'],'strength':result['strength_decision']['value'],'structure':result['structure_decision']['value'],'domains':len(result['domain_positions'])},ensure_ascii=False))
    raise SystemExit(1 if a.strict and result['status']!='ok' else 0)
if __name__=='__main__': main()
