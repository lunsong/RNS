from RNS import *
import numpy as np
from time import gmtime
from quark_eos import quark_eos
from scipy.optimize import fminbound

rns = RNS(MDIV=65, SDIV=101)

#rns.eos = load_quark_eos(1., 1.235, .3,"eosNL3")
rns.eos = quark_eos(1,1.6,1.3,cons="Maxwell-Gibbs", ss1=1.,Gama=1.03)

#rns.hierarchy.length[:] = [.02, .04, .08]

rns.p_surface = 1e-8

dr = .05
rns.cf = 1.
rns.acc = 1e-7
rns.r_ratio = .7
rns.criteria = 6
rns.max_refine = 20
rns.throw = False
no_refine = False
M0 = None
name = "b"
task = None
no_save = True
if task=="M0":
    dec = 2e-2
else:
    dec = 2e-1

rns.ec = rns.e1 + 1e-3 
end_ec = rns.e1 + dec * 10

if task == "TOV_max_M":
    rns.ec = 2.1
    end_ec = 5.0

load = lambda name: np.load(f"out/{name}.npy")



date = gmtime()
name = f"out/{date.tm_mon}{date.tm_mday}-{name}-{task}"


#if not (rns.eos.start > 0 and rns.ec > rns.e0):
if no_refine:
    rns.max_n = 100
    rns.max_refine = 0

#M0 = 4.0499032269470835e+32

if rns.r_ratio < .8:
    r_ratio = rns.r_ratio
    rns.spin(.8)
    rns.spin(r_ratio)

if task == "TOV_max_M":
    ec, M, conv, fcalls = fminbound(lambda x: -rns.spin(.9999,x).M/msol,
            rns.ec, end_ec, disp=3, full_output=True)
    print(ec, M)
    task=None

elif task == "stable":
    rns.spin(rns.r_ratio, rns.e1 + 1e-3)
    print(rns.is_stable())
    task=None


series = []
dtype = np.dtype([
    ("M",float),
    ("M0",float),
    ("r_ratio",float),
    ("R",float),
    ("Omega",float),
    ("Omega_K",float),
    ("J",float),
    ("T",float),
    ("Mp",float),
    ("ec",float)])

if task != None:
    try: 

        if task == "sweap":
            rns.spin(.9999)
            while rns.ec < end_ec:
                print('ec=',rns.ec)
                #while rns.Omega.value < rns.Omega_K.value and rns.M0.value < M0:
                while rns.Omega.value < rns.Omega_K.value:
                    print("r=",rns.r_ratio)
                    series.append(rns.values)
                    rns.spin(rns.r_ratio - dr)
                rns.spin(rns.r_ratio, rns.ec + dec)
                if rns.ec > end_ec: break
                print('ec=',rns.ec)
                for r_ratio in np.mgrid[rns.r_ratio:.9999:dr]:
                    print("r=",r_ratio)
                    series.append(rns.spin(r_ratio))
                rns.spin(rns.r_ratio, rns.ec + dec)

        elif task == "TOV":
            while rns.ec < end_ec:
                series.append(rns.spin(1.))
                print(f"ec={rns.ec} R={rns.values.R} "\
                      f"M={rns.values.M/msol}")
                rns.ec += dec

        elif task == "ec":
            for r_ratio in np.linspace(.999,.7,20):
                series.append(rns.spin(r_ratio))
        elif task == "M0":
            rns.spin(rns.r_ratio)
            for stat in rns.spin_down(end_ec, dec, M0, disp=True):
                series.append(stat.values)

    except (Exception,KeyboardInterrupt) as E:
        series = np.array(series, dtype)
        if not no_save: np.save(name, series)
        raise E

    series = np.array(series, dtype)
    if not no_save: np.save(name, series)
