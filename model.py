"""
Passive cold chain for tomatoes in transit: techno-economic model
Feranmi Adedipe, follow-on to B.Sc. Chemical Engineering thesis (University of Lagos)

The service: an operator owns a pool of insulated containers lined with sealed panels
of the thesis PCM (a modified Glauber's salt that melts at ~15 °C). At an origin hub
near the farms, produce is pre-cooled and loaded into containers with freshly charged
PCM. The containers ride on ordinary trucks to Lagos, are emptied at the market, and
come back on return trucks to be recharged. The shipper pays a fee per container-trip.

What it answers
  1. Thermal: how much PCM does a container need for the trip, and how much produce
     still fits? (50 L crate vs 500 L bin)
  2. Logistics: how much truck space does the cold chain cost, and how many
     containers must the pool hold for the round trip?
  3. Finance: what fee per trip breaks even, and what does it cost in total to move
     1 kg of tomatoes at <=15 °C, compared with an open basket and a refrigerated truck?
     Each lever (sourcing, container, rate, currency, grant, chemistry) is tested
     on its own.

Every input sits in A with a tag:
  [thesis]  measured in the thesis           [quote]  Lagos supplier price, Oct 2026
  [market]  published data (see README)      [est]    estimate: replace with a real quote

Run:  python model.py          (needs numpy only)
"""
import copy
import math
import numpy as np

A = dict(
    # ---------- PCM, from the thesis ----------
    latent_kJkg=87.0,            # [thesis] melting enthalpy, standard T-history (85-89 J/g)
    latent_ideal_kJkg=192.0,     # [thesis] expected if decahydrate forms fully (190-195 J/g)
    t_melt=15.3,                 # [thesis] melting temperature, °C
    t_nucleation=0.8,            # [thesis] supercools to ~0.8 °C before crystallising
    cp_solid=2.2,                # [thesis] assumed composite cp, kJ/kg·K (1.9-2.5)
    cp_liquid=3.3,               # [thesis] assumed composite cp, kJ/kg·K (3.0-3.6)
    pcm_density=1.5,             # [est] kg/L
    recipe={"Na2SO4": 0.3494, "H2O": 0.4428, "NaCl": 0.0757,      # [thesis] Re-run 2,
            "NH4Cl": 0.0245, "borax": 0.0110, "CMC": 0.0966},     # in-situ hydration
    price_lab={"Na2SO4": 5_000, "H2O": 100, "NaCl": 18_000,       # [quote] NGN/kg from
               "NH4Cl": 26_000, "borax": 2_800, "CMC": 5_600},    # 500 g-25 kg packs
    price_bulk={"Na2SO4": 2_500, "H2O": 100, "NaCl": 1_200,       # [est] technical grade,
                "NH4Cl": 6_000, "borax": 2_800, "CMC": 5_600},    # 25-50 kg: get quotes

    # ---------- containers ----------
    containers={
        "crate_50L": dict(label="50 L crate", inner=(0.50, 0.33, 0.30), wall=0.05,
                          cost=35_000, empty_kg=6.0, produce_cap_kg=20.0, pack=0.85,       # [est]
                          loss_pct=0.12, ships_back=True),
        "bin_500L": dict(label="500 L bin", inner=(0.80, 0.80, 0.80), wall=0.075,
                         cost=280_000, empty_kg=40.0, produce_cap_kg=250.0, pack=0.80,     # [est]
                         loss_pct=0.08, ships_back=True),
        # insulated trailer body lined with PCM plates: a refrigerated truck with no
        # cooling unit. Size comes from the route; it returns with the truck.
        "truck_body": dict(label="PCM truck", is_truck=True, wall=0.08,
                           cost=30_000_000, empty_kg=3_500.0, pack=1.0,                   # [est]
                           loss_pct=0.02, ships_back=False),
    },
    k_insulation=0.025,          # [est] polyurethane foam, W/m·K
    edge_factor=1.3,             # [est] corners, lid seal, thermal bridges
    panel_overhead=1.15,         # [est] panel walls and air gaps around the PCM
    panel_kg=2.0, panel_cost=1_500,   # [est] one sealed HDPE panel holds 2 kg PCM
    sets_per_container=1.1,      # the set travels with the container; 10% spares
    produce_bulk_density=0.50,   # [est] kg/L, tomatoes in a container
    cp_produce=3.9,              # [est] kJ/kg·K
    respiration_W_per_kg=0.04,   # [est] tomatoes near 15 °C
    t_hold=14.0,                 # target produce temperature in transit, °C
    t_precool=15.0,              # [est] produce temperature leaving the pre-cooler
    t_load=26.0,                 # [est] produce temperature at the hub after morning harvest
    t_panel_load=8.0,            # [est] panels warmed to 8 °C before loading (chill injury)
    safety=1.10,                 # 10% thermal margin on the trip

    # ---------- routes ----------
    routes={
        "long_haul": dict(label="Kaduna/Kano tomato belt -> Mile 12, Lagos",
                          trip_h=40, t_ambient=30.0, cycle_days=6,       # [est] reefer took ~2 days
                          truck_cost=2_000_000,                          # [market] trailer load, May 2026
                          truck_m3=60, truck_t=30, basket_t=25,          # [est]
                          reefer_kg=18_660, reefer_multiple=2.0,         # [market] 933 x 20 kg; ~2x cost
                          body_inner=(12.0, 2.35, 2.40), body_cap_kg=18_660,   # [est] 40 ft body
                          return_share=0.30, pv_yield=5.0),              # [est] north: strong sun
        "regional": dict(label="Oyo/Ogun farms -> Lagos",
                         trip_h=10, t_ambient=31.0, cycle_days=2,
                         truck_cost=400_000, truck_m3=30, truck_t=15, basket_t=12,   # [est]
                         reefer_kg=9_000, reefer_multiple=2.0,
                         body_inner=(6.5, 2.30, 2.30), body_cap_kg=9_000,     # [est] 10 t truck
                         return_share=0.30, pv_yield=4.0),
    },

    # ---------- origin hub: pre-cooling + PCM charging ----------
    hub_t_per_day=3.0,           # produce dispatched per hub per day at full use (pilot)
    precool_cost_per_tday=6_000_000,     # [est] cold room + refrigeration per t/day
    freezer_cost_per_tpcm_day=3_600_000, # [est] blast freezer per t of PCM charged/day
    cop_cool=2.0, cop_freeze=1.3,        # [est]
    cooling_loss_factor=1.3, charge_loss_factor=1.4,
    t_return=20.0,               # [est] PCM temperature when containers come back
    t_freezer=-3.0,              # [est] PCM must go below 0.8 °C to crystallise
    pv_cost_per_kWp=550_000, battery_cost_per_kWh=300_000,   # [est]
    civil_cost=6_000_000, depot_cost=3_000_000,              # [est] origin works; Lagos depot
    grid_share=0.20, tariff=210,                             # [est]

    # ---------- operations ----------
    fee=1_500,                   # NGN per 20 kg-equivalent per trip (scaled by produce carried)
    days=300,
    util_ramp=[0.45, 0.65, 0.80, 0.80, 0.80],    # [est] share of hub capacity sold
    staff=6, salary_month=180_000,               # [est] 4 at origin, 2 at the Lagos depot
    site_rent=3_600_000,                         # [est]
    collection_pct=0.015, maintenance_pct=0.03,  # [est]
    pcm_refresh_pct=0.30,        # [est] PCM replaced per year (grade-2 separation)
    overhead=9_600_000,          # [est] manager and finance, per venture per year
    inflation=0.12,              # [market/est] Sept 2026 CPI 14.63%, assumed to ease
    salvage_pct=0.40,            # [est] hub value left after 5 years

    # ---------- shipper's side ----------
    loss_cut_pp=0.10,            # [est] cooled transit cuts loss by 10 points (transit + first days at market)
    prices_per_kg={"glut": 350, "average": 1_000, "scarcity": 2_400},   # [market] Mile 12, 2024-26

    # ---------- tax (Nigeria Tax Act 2025) [market] ----------
    small_turnover=100e6, small_assets=250e6, tax_rate=0.34, dep_years=5,

    # ---------- financing [market/est] ----------
    debt_share=0.60, cost_equity=0.35,
    kd_commercial=0.31,          # [market] bank prime rates 25.5-31% (mid-2026)
    kd_usd=0.07, fx_depreciation=0.10, fx_stress=0.30,   # [est]
    kd_local_concessional=0.14,  # [est] naira concessional or currency-hedged facility
    grant_pct=0.25, tax_shield=0.30,
)

# ======================================================================
# 1. THERMAL + CONTAINER SIZING
# ======================================================================
def resolve(c, route):
    """A truck body takes its size from the route."""
    if c.get("is_truck"):
        c = dict(c, inner=route["body_inner"], produce_cap_kg=route["body_cap_kg"])
    return c

def geometry(a, c):
    L, W, H = c["inner"]
    t = c["wall"]
    a_in = 2 * (L * W + L * H + W * H)
    Lo, Wo, Ho = L + 2 * t, W + 2 * t, H + 2 * t
    a_out = 2 * (Lo * Wo + Lo * Ho + Wo * Ho)
    UA = a["k_insulation"] / t * math.sqrt(a_in * a_out) * a["edge_factor"]
    return UA, L * W * H * 1000, Lo * Wo * Ho          # W/K, inner litres, outer m3

def usable_kJ_per_kg(a, latent):
    return latent + a["cp_solid"] * (a["t_melt"] - a["t_panel_load"])

def size_container(a, c, route, latent=None):
    """PCM needed to hold the trip, and the produce that still fits beside it."""
    latent = a["latent_kJkg"] if latent is None else latent
    c = resolve(c, route)
    UA, inner_L, outer_m3 = geometry(a, c)
    produce = c["produce_cap_kg"]
    for _ in range(100):
        leak_W = UA * (route["t_ambient"] - a["t_hold"]) + a["respiration_W_per_kg"] * produce
        need = produce * a["cp_produce"] * max(0.0, a["t_precool"] - a["t_hold"]) + leak_W * route["trip_h"] * 3.6
        pcm = need * a["safety"] / usable_kJ_per_kg(a, latent)
        room = inner_L - pcm / a["pcm_density"] * a["panel_overhead"]
        produce = min(c["produce_cap_kg"], max(0.0, room * a["produce_bulk_density"]))
    panels = math.ceil(pcm / a["panel_kg"])
    gross = produce + pcm + c["empty_kg"] + panels * 0.15
    return dict(UA=UA, leak_W=leak_W, pcm=pcm, produce=produce, panels=panels,
                gross_kg=gross, outer_m3=outer_m3, inner_L=inner_L)

def per_truck(a, c, route, s):
    if c.get("is_truck"):
        return 1
    by_vol = route["truck_m3"] * c["pack"] / s["outer_m3"]
    by_wt = route["truck_t"] * 1000 / s["gross_kg"]
    return math.floor(min(by_vol, by_wt))

# ======================================================================
# 2. COSTS
# ======================================================================
def pcm_cost_per_kg(a, prices):
    return sum(a["recipe"][k] * prices[k] for k in a["recipe"])

def charge_kJ_per_kg(a, latent):
    return (a["cp_liquid"] * (a["t_return"] - a["t_nucleation"]) + latent
            + a["cp_solid"] * (a["t_nucleation"] - a["t_freezer"])) * a["charge_loss_factor"]

def setup(a, ckey="crate_50L", rkey="long_haul", prices="lab", latent=None, supercool_fixed=False):
    """Everything per hub that does not depend on the year."""
    latent = a["latent_kJkg"] if latent is None else latent
    r = a["routes"][rkey]
    c = resolve(a["containers"][ckey], r)
    p = a["price_lab"] if prices == "lab" else a["price_bulk"]
    s = size_container(a, c, r, latent)
    n_truck = per_truck(a, c, r, s)
    freight = r["truck_cost"] / n_truck                       # forward freight per container
    set_cost = s["pcm"] * pcm_cost_per_kg(a, p) + s["panels"] * a["panel_cost"]
    sets = 1.0 if c.get("is_truck") else a["sets_per_container"]
    slot_cost = c["cost"] + sets * set_cost
    dispatch = a["hub_t_per_day"] * 1000 / s["produce"]       # containers per day at full use
    spare = 1.0 if c.get("is_truck") else 1.10
    pool = math.ceil(dispatch * r["cycle_days"] * spare)
    precool_kWh = (a["hub_t_per_day"] * 1000 * a["cp_produce"] * (a["t_load"] - a["t_precool"])
                   * a["cooling_loss_factor"] / a["cop_cool"] / 3600)
    pcm_t_day = dispatch * s["pcm"] / 1000
    cop = a["cop_cool"] if supercool_fixed else a["cop_freeze"]
    charge_kWh = pcm_t_day * 1000 * charge_kJ_per_kg(a, latent) / cop / 3600
    kWh = precool_kWh + charge_kWh
    parts = {"pre-cooler": a["precool_cost_per_tday"] * a["hub_t_per_day"] * (1.2 if supercool_fixed else 1.0),
             "PCM freezer": 0.0 if supercool_fixed else a["freezer_cost_per_tpcm_day"] * pcm_t_day,
             "solar PV": kWh / r["pv_yield"] * a["pv_cost_per_kWp"],
             "battery": 0.5 * precool_kWh * a["battery_cost_per_kWh"],
             "civil + Lagos depot": a["civil_cost"] + a["depot_cost"]}
    hub = sum(parts.values())
    return dict(c=c, r=r, s=s, n_truck=n_truck, freight=freight, set_cost=set_cost, slot_cost=slot_cost,
                dispatch=dispatch, pool=pool, kWh=kWh, hub=hub, parts=parts, p=p,
                capex=hub + pool * slot_cost)

# ======================================================================
# 3. CASH FLOWS
# ======================================================================
def cash_flows(a, S, hub_starts=(0,), fee=None, grant=0.0):
    """Nominal NGN free cash flow, years 0..5. fee is per trip of one container."""
    fee_trip = (a["fee"] if fee is None else fee)
    years = 6
    capex = np.zeros(years); rev = np.zeros(years); opex = np.zeros(years); salvage = np.zeros(years)
    for st in hub_starts:
        e0 = (1 + a["inflation"]) ** st
        capex[st] += S["capex"] * e0 * (1 - grant)
        salvage[-1] += a["salvage_pct"] * S["hub"] * e0 * (1 - grant)
        for y in range(st + 1, years):
            u = a["util_ramp"][min(y - st - 1, len(a["util_ramp"]) - 1)]
            e = (1 + a["inflation"]) ** (y - 1)
            trips = S["dispatch"] * u * a["days"]
            r = trips * fee_trip * e
            rev[y] += r
            o = r * a["collection_pct"]
            o += (a["staff"] * a["salary_month"] * 12 + a["site_rent"] + a["maintenance_pct"] * S["hub"]) * e
            o += S["kWh"] * u * a["grid_share"] * a["days"] * a["tariff"] * e
            if S["c"]["ships_back"]:                                        # empties back to the hub
                o += trips * S["r"]["return_share"] * S["freight"] * e
            o += S["pool"] * (a["pcm_refresh_pct"] * a["sets_per_container"] * S["s"]["pcm"]
                              * pcm_cost_per_kg(a, S["p"]) + S["c"]["loss_pct"] * S["slot_cost"]) * e
            opex[y] += o
    opex[1:] += a["overhead"] * (1 + a["inflation"]) ** np.arange(0, years - 1)
    ebitda = rev - opex
    dep = np.zeros(years)
    for y in range(years):
        for k in range(y + 1, min(y + 1 + a["dep_years"], years)):
            dep[k] += capex[y] / a["dep_years"]
    tax = np.zeros(years); carry = 0.0
    for y in range(1, years):
        small = rev[y] < a["small_turnover"] and capex[: y + 1].sum() < a["small_assets"]
        taxable = ebitda[y] - dep[y] + carry
        carry = min(0.0, taxable)
        if taxable > 0 and not small:
            tax[y] = taxable * a["tax_rate"]
    return dict(fcf=ebitda - tax - capex + salvage, rev=rev, ebitda=ebitda, capex=capex)

def npv(rate, cf):
    return float(np.sum(cf / (1 + rate) ** np.arange(len(cf))))

def irr(cf, lo=-0.95, hi=5.0):
    f = lambda r: npv(r, cf)
    if f(lo) * f(hi) > 0:
        return float("nan")
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(lo) * f(mid) > 0 else (lo, mid)
    return (lo + hi) / 2

def wacc(a, kd):
    return a["debt_share"] * kd * (1 - a["tax_shield"]) + (1 - a["debt_share"]) * a["cost_equity"]

def breakeven_fee(a, S, rate, **kw):
    lo, hi = 1.0, 2_000_000.0
    for _ in range(120):
        mid = (lo + hi) / 2
        if npv(rate, cash_flows(a, S, fee=mid, **kw)["fcf"]) < 0:
            lo = mid
        else:
            hi = mid
    return hi

def all_in_per_kg(a, S, rate, **kw):
    """Break-even fee + forward freight, per kg of produce delivered cool."""
    fee = breakeven_fee(a, S, rate, **kw)
    return (fee + S["freight"]) / S["s"]["produce"], fee

def precool_per_kg(a, r, rate):
    """Cost per kg of a pre-cooling hub on its own (a reefer needs one too)."""
    kWh = (a["hub_t_per_day"] * 1000 * a["cp_produce"] * (a["t_load"] - a["t_precool"])
           * a["cooling_loss_factor"] / a["cop_cool"] / 3600)
    capex = (a["precool_cost_per_tday"] * a["hub_t_per_day"] + kWh / r["pv_yield"] * a["pv_cost_per_kWp"]
             + 0.5 * kWh * a["battery_cost_per_kWh"] + a["civil_cost"])
    crf = rate / (1 - (1 + rate) ** -5)
    opex = 3 * a["salary_month"] * 12 + a["site_rent"] / 2 + a["maintenance_pct"] * capex
    kg = a["hub_t_per_day"] * 1000 * a["days"] * a["util_ramp"][-1]
    return (capex * crf + opex) / kg

def benchmarks(a, r, rate):
    basket = r["truck_cost"] / (r["basket_t"] * 1000)
    reefer = r["reefer_multiple"] * r["truck_cost"] / r["reefer_kg"] + precool_per_kg(a, r, rate)
    return basket, reefer

# ======================================================================
# 4. REPORT
# ======================================================================
def m(x):
    return f"{x/1e6:,.1f}M"

def report(a=A):
    out = []; p = out.append
    rates = {
        "A  Commercial naira debt": wacc(a, a["kd_commercial"]),
        "B  USD concessional, unhedged": wacc(a, (1 + a["kd_usd"]) * (1 + a["fx_depreciation"]) - 1),
        "B* same, devaluation stress": wacc(a, (1 + a["kd_usd"]) * (1 + a["fx_stress"]) - 1),
        "C  Naira concessional/hedged": wacc(a, a["kd_local_concessional"]),
    }
    rA, rC = rates["A  Commercial naira debt"], rates["C  Naira concessional/hedged"]
    SCALE = dict(hub_starts=(0, 1, 1, 1))

    for rkey, r in a["routes"].items():
        basket, reefer = benchmarks(a, r, rC)
        p("=" * 84)
        p(f"ROUTE: {r['label']}  ({r['trip_h']} h trip, {r['t_ambient']:.0f} °C mean, "
          f"{r['cycle_days']}-day round trip)")
        p("=" * 84)
        p(f"Benchmarks per kg delivered: open basket {basket:,.0f} NGN (warm); refrigerated truck "
          f"+ pre-cooling {reefer:,.0f} NGN (cold)")
        p("\n1. CONTAINER SIZING (thesis PCM, 87 J/g; produce pre-cooled to 15 °C)")
        for ck, c0 in a["containers"].items():
            c = resolve(c0, r)
            s = size_container(a, c, r)
            S = setup(a, ck, rkey, "bulk")
            p(f"  {c['label']:10s} leak {s['leak_W']:6.1f} W | PCM {s['pcm']:7.1f} kg | produce "
              f"{s['produce']:8.1f} kg | PCM per kg produce {s['pcm']/s['produce']:4.2f} | "
              f"{S['n_truck']:3d} per truck = {S['n_truck']*s['produce']/1000:4.1f} t | "
              f"freight {S['freight']/s['produce']:4.0f} NGN/kg")
        s_bad = dict(a); s_bad["t_precool"] = a["t_load"]
        sc = size_container(s_bad, a["containers"]["crate_50L"], r)
        p(f"  Without pre-cooling (loaded at {a['t_load']:.0f} °C) a 50 L crate needs "
          f"{sc['pcm']:.1f} kg of PCM for {sc['produce']:.1f} kg of produce.")

        p("\n2. ONE HUB (3 t of produce a day), bulk chemicals")
        for ck in a["containers"]:
            S = setup(a, ck, rkey, "bulk")
            p(f"  {S['c']['label']:10s} {S['dispatch']:6.2f} units/day, pool {S['pool']:5,d}, "
              f"unit + PCM {S['slot_cost']:12,.0f} NGN, hub {m(S['hub'])}, total capex {m(S['capex'])}")

        p("\n3. ALL-IN COST PER KG DELIVERED AT <=15 °C (break-even fee + freight), 4 hubs")
        p(f"  {'':56s}{'NGN/kg':>7}{'change':>8}")
        G = dict(grant=a["grant_pct"])
        steps = [
            ("As tested: 50 L crates, lab chemicals, freezer, bank debt", dict(ckey="crate_50L", prices="lab"), {}, rA),
            ("+ bulk chemicals", dict(ckey="crate_50L", prices="bulk"), {}, rA),
            ("+ 500 L bins instead of crates", dict(ckey="bin_500L", prices="bulk"), {}, rA),
            ("+ one PCM-lined truck body instead of bins", dict(ckey="truck_body", prices="bulk"), {}, rA),
            ("+ naira concessional debt", dict(ckey="truck_body", prices="bulk"), {}, rC),
            ("+ 25% capex grant", dict(ckey="truck_body", prices="bulk"), G, rC),
            ("+ fix supercooling: charge in the pre-cooler, no freezer",
             dict(ckey="truck_body", prices="bulk", supercool_fixed=True), G, rC),
            ("+ fix phase separation (~190 J/g)",
             dict(ckey="truck_body", prices="bulk", supercool_fixed=True, latent=a["latent_ideal_kJkg"]), G, rC),
        ]
        prev = None
        for label, skw, ckw, rate in steps:
            S = setup(a, rkey=rkey, **skw)
            per_kg, fee = all_in_per_kg(a, S, rate, **SCALE, **ckw)
            d = "" if prev is None else f"{per_kg - prev:+8.0f}"
            p(f"  {label:56s}{per_kg:7.0f}{d:>8}")
            prev = per_kg
        best = prev
        p(f"  {'Refrigerated truck + pre-cooling (benchmark)':56s}{reefer:7.0f}")
        p(f"  {'Open basket, no cooling (benchmark)':56s}{basket:7.0f}")

        p("\n4. FINANCING ALONE (PCM truck, bulk chemicals, 4 hubs): all-in NGN/kg by WACC")
        S = setup(a, "truck_body", rkey, "bulk")
        for rn, rv in rates.items():
            per_kg, _ = all_in_per_kg(a, S, rv, **SCALE)
            per_kg_g, _ = all_in_per_kg(a, S, rv, **G, **SCALE)
            p(f"  {rn:31s} WACC {rv:5.1%}   {per_kg:5.0f} | with 25% grant {per_kg_g:5.0f}")

        p(f"\n5. IS IT WORTH IT TO THE SHIPPER? (cooling cuts loss by {a['loss_cut_pp']:.0%} points)")
        p("   premium = cost per kg above an open basket")
        today, _ = all_in_per_kg(a, setup(a, "truck_body", rkey, "bulk"), rA, **SCALE)
        for season, price in a["prices_per_kg"].items():
            saved = price * a["loss_cut_pp"]
            p(f"  {season:9s} ({price:5,} NGN/kg): saves {saved:4.0f} | premium: PCM truck, bank debt "
              f"{today - basket:4.0f}; all fixes {best - basket:4.0f}; reefer {reefer - basket:4.0f}")
        p("")

    p("=" * 84)
    p("SENSITIVITY: long haul, PCM truck, bulk chemicals, bank debt, 4 hubs (NGN/kg delivered cool)")
    p("=" * 84)
    def truck_vs_reefer(b):
        rb = b["routes"]["long_haul"]
        ra = wacc(b, b["kd_commercial"])
        per_kg, _ = all_in_per_kg(b, setup(b, "truck_body", "long_haul", "bulk"), ra, hub_starts=(0, 1, 1, 1))
        return per_kg, benchmarks(b, rb, ra)[1]
    base_t, base_r = truck_vs_reefer(a)
    p(f"  {'Base case':44s} PCM truck {base_t:5.0f} | reefer {base_r:5.0f}")
    tests = [
        ("Truck body conversion 15M / 60M NGN", lambda b, v: b["containers"]["truck_body"].update(cost=v), (15e6, 60e6)),
        ("Hub size 1.5 / 18.7 t a day (one truck daily)", lambda b, v: b.update(hub_t_per_day=v), (1.5, 18.7)),
        ("Trip 30 h / 60 h", lambda b, v: b["routes"]["long_haul"].update(trip_h=v), (30, 60)),
        ("Reefer costs 1.5x / 2.5x normal haulage", lambda b, v: b["routes"]["long_haul"].update(reefer_multiple=v), (1.5, 2.5)),
        ("Produce respiration 0.02 / 0.06 W/kg", lambda b, v: b.update(respiration_W_per_kg=v), (0.02, 0.06)),
        ("Mean ambient on the road 27 / 33 °C", lambda b, v: b["routes"]["long_haul"].update(t_ambient=v), (27.0, 33.0)),
    ]
    for label, setter, (lo, hi) in tests:
        vals = []
        for v in (lo, hi):
            b = copy.deepcopy(a); setter(b, v); vals.append(truck_vs_reefer(b))
        p(f"  {label:44s} PCM truck {vals[0][0]:5.0f} / {vals[1][0]:5.0f} | reefer {vals[0][1]:5.0f} / {vals[1][1]:5.0f}")
    print("\n".join(out))

if __name__ == "__main__":
    report()
