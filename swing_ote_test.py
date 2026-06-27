"""
Does the Swing OTE tool's DAILY bias gate hold up vs the validated 1H gate?
Same validated MS+OTE engine (5m structure, piv4, deep 0.79, stop 0.15ATR, maxWait15, RR2.5,
FVG/OB-in-zone confluence). Only the BIAS source changes. Real NQ=F 5m, 58d, 0.02R cost,
SL-first, one-at-a-time. H1/H2 = OOS halves, L/S = long/short.
NOTE: ~276 bars/day, so daily EMA20/50 = ema(5520/13800) — EMA50d never warms on 58d.
Validated 1H gate ema(600/1200) ~= a 2.2d / 4.3d trend (already daily-ish).
"""
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import proxy_backtest as pb
from omg_test import loadv, et_day
from ms_ote_test import pivots

COST=0.02

def run(T,O,H,L,C, ef_len, es_len, piv=4, oteFib=0.79, stopBuf=0.15, rr=2.5, maxWait=15,
        conf='grade'):
    pb.T,pb.O,pb.H,pb.L,pb.C=T,O,H,L,C; pb.n=len(C); pb.ATR=pb.atr(14)
    ATR=pb.ATR; n=len(C)
    if ef_len is None:                 # no bias gate
        up=lambda i: True; dn=lambda i: True
    else:
        ef=pb.ema(C,ef_len); es=pb.ema(C,es_len)
        up=lambda i: ef[i] is not None and es[i] is not None and ef[i]>es[i]
        dn=lambda i: ef[i] is not None and es[i] is not None and ef[i]<es[i]
    ph,pl=pivots(H,L,piv)

    def fvg_in(a,b,lo,hi,bull):
        for k in range(a+2,b+1):
            if bull and L[k]>H[k-2]: glo,ghi=H[k-2],L[k]
            elif (not bull) and H[k]<L[k-2]: glo,ghi=H[k],L[k-2]
            else: continue
            if ghi>=lo and glo<=hi: return True
        return False
    def ob_in(a,b,lo,hi,bull):
        for k in range(b,a-1,-1):
            opp=(C[k]<O[k]) if bull else (C[k]>O[k])
            if not opp: continue
            blo,bhi=min(O[k],C[k]),max(O[k],C[k])
            if bhi>=lo and blo<=hi: return True
        return False
    def has_conf(a,b,lo,hi,bull):
        return fvg_in(a,b,lo,hi,bull) or ob_in(a,b,lo,hi,bull)

    res=[]
    lastSH=lastSL=lastSHbar=lastSLbar=None
    armL=armS=None; usedSH=usedSL=None; pos=None
    for i in range(n):
        A=ATR[i]
        if i>0 and et_day(T[i])!=et_day(T[i-1]): armL=armS=None
        if pos is not None and i>pos['start']:
            if pos['dir']==1:
                if L[i]<=pos['s']: res.append((-1.0-COST,1,pos['ts'],pos['c'])); pos=None
                elif H[i]>=pos['t']: res.append((pos['rr']-COST,1,pos['ts'],pos['c'])); pos=None
            else:
                if H[i]>=pos['s']: res.append((-1.0-COST,-1,pos['ts'],pos['c'])); pos=None
                elif L[i]<=pos['t']: res.append((pos['rr']-COST,-1,pos['ts'],pos['c'])); pos=None
        j=i-piv
        if j>=0:
            if ph[j]: lastSH=H[j]; lastSHbar=j
            if pl[j]: lastSL=L[j]; lastSLbar=j
        if A==A and A>0 and lastSH is not None and lastSL is not None:
            if C[i]>lastSH and lastSHbar!=usedSH and lastSLbar is not None and lastSL<lastSH and lastSLbar<i and up(i):
                legLow=min(L[lastSLbar:i+1]); legHigh=max(H[lastSLbar:i+1]); rng=legHigh-legLow
                if rng>0:
                    top=legHigh-0.62*rng; bot=legHigh-0.79*rng
                    cf=has_conf(lastSLbar,i,bot,top,True)
                    armL=dict(entry=legHigh-oteFib*rng,legLow=legLow,legHigh=legHigh,born=i,ts=T[i],cf=cf); usedSH=lastSHbar
            if C[i]<lastSL and lastSLbar!=usedSL and lastSHbar is not None and lastSH>lastSL and lastSHbar<i and dn(i):
                legHigh=max(H[lastSHbar:i+1]); legLow=min(L[lastSHbar:i+1]); rng=legHigh-legLow
                if rng>0:
                    top=legLow+0.79*rng; bot=legLow+0.62*rng
                    cf=has_conf(lastSHbar,i,bot,top,False)
                    armS=dict(entry=legLow+oteFib*rng,legLow=legLow,legHigh=legHigh,born=i,ts=T[i],cf=cf); usedSL=lastSHbar
        if armL is not None and (i-armL['born']>maxWait or C[i]<armL['legLow']): armL=None
        if armS is not None and (i-armS['born']>maxWait or C[i]>armS['legHigh']): armS=None
        if pos is None and A==A and A>0:
            if armL is not None and L[i]<=armL['entry'] and i>armL['born']:
                e=armL['entry']; s=armL['legLow']-stopBuf*A; risk=e-s
                if risk>0:
                    pos=dict(dir=1,s=s,t=e+rr*risk,rr=rr,start=i,ts=armL['ts'],c=armL['cf'])
                armL=None
            elif armS is not None and H[i]>=armS['entry'] and i>armS['born']:
                e=armS['entry']; s=armS['legHigh']+stopBuf*A; risk=s-e
                if risk>0:
                    pos=dict(dir=-1,s=s,t=e-rr*risk,rr=rr,start=i,ts=armS['ts'],c=armS['cf'])
                armS=None
    return res

nb=loadv("NQ")
T=[x[0] for x in nb]; O=[x[1] for x in nb]; H=[x[2] for x in nb]; L=[x[3] for x in nb]; C=[x[4] for x in nb]
MID=T[len(T)//2]
ev=lambda rs: pb.stats([r[0] for r in rs])
f=lambda s: f"{s['exp']:+.2f}/{s['pf']:.2f}" if s else "  -  "
def show(tag, rs):
    full=ev(rs)
    if not full: print(f"  {tag:<24} (no trades)"); return
    h1=ev([r for r in rs if r[2]<MID]); h2=ev([r for r in rs if r[2]>=MID])
    lo=ev([r for r in rs if r[1]==1]); sh=ev([r for r in rs if r[1]==-1])
    print(f"  {tag:<24} n={full['trades']:>3} win={full['win']:4.0f}% exp/PF={f(full)}  H1={f(h1)} H2={f(h2)}  L={f(lo)} S={f(sh)}")

BPD=276
print("#"*104)
print("# Swing OTE bias-source test (validated 5m engine, only the bias gate changes) — real NQ=F 5m, 58d")
print("#"*104)
print("\n### BIAS SOURCE (all trades, no confluence filter) ###")
show("none (no gate)",        run(T,O,H,L,C, None, None))
show("1H 600/1200 (validated)",run(T,O,H,L,C, 600, 1200))
show("daily ~1d/2d",          run(T,O,H,L,C, BPD, BPD*2))
show("daily ~2d/4d",          run(T,O,H,L,C, BPD*2, BPD*4))
show("daily ~5d/10d",         run(T,O,H,L,C, BPD*5, BPD*10))

print("\n### CONFLUENCE grade split under the validated 1H gate (WITH vs WITHOUT FVG/OB) ###")
rs=run(T,O,H,L,C, 600, 1200, conf='grade')
wi=[r for r in rs if r[3]]; wo=[r for r in rs if not r[3]]
print(f"  WITH FVG/OB  n={len(wi):>3} {f(ev(wi))}   |  WITHOUT n={len(wo):>3} {f(ev(wo))}")
print("\n### CONFLUENCE grade split under a daily ~2d/4d gate ###")
rs=run(T,O,H,L,C, BPD*2, BPD*4, conf='grade')
wi=[r for r in rs if r[3]]; wo=[r for r in rs if not r[3]]
print(f"  WITH FVG/OB  n={len(wi):>3} {f(ev(wi))}   |  WITHOUT n={len(wo):>3} {f(ev(wo))}")
