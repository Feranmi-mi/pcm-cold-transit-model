# Passive cold chain for tomatoes in transit: a techno-economic model

This model asks whether the phase change material (PCM) from my B.Sc. thesis can keep tomatoes cool on the road from the northern farms to Lagos, without a diesel refrigeration unit. The PCM is a modified sodium sulphate decahydrate (Glauber's salt) that melts at about 15 °C, close to the temperature tomatoes should travel at.

Short answer: **yes, if the PCM lines one insulated truck body rather than many small crates.**
- On the 40-hour haul from Kaduna/Kano to Mile 12, a PCM-lined truck delivers tomatoes at ≤15 °C for about **₦200/kg**.
- A refrigerated truck with the same pre-cooling costs about **₦240/kg**.
- Small insulated crates cost about **₦500/kg**.

The comparison depends on the price of a refrigerated truck, which needs a current quote.

## Key findings (long haul, Kaduna/Kano → Lagos)

**1. Produce must be pre-cooled first.**
- Both a PCM container and a refrigerated truck hold cold; neither is built to pull warm produce down.
- Loaded at 26 °C without pre-cooling, a 50 L crate needs 25 kg of PCM to carry 15 kg of tomatoes.
- So the origin hub needs a pre-cooler as well as PCM charging.

**2. Container size decides the economics.** Each small container carries its own insulation, which takes truck space away from produce.

| Container | PCM per kg of produce | Produce per truck | Freight per kg |
|---|---:|---:|---:|
| 50 L crate | 1.06 kg | 8.7 t | ₦230 |
| 500 L bin | 0.32 kg | 12.6 t | ₦159 |
| PCM-lined truck body | 0.17 kg | 18.7 t | ₦107 |
| Open baskets, no cooling | n/a | 25 t | ₦80 |

**3. What each step is worth.** All-in cost per kg delivered at ≤15 °C (break-even fee plus freight, four hubs). Each step is added to the one before.

| Step | ₦/kg | Change |
|---|---:|---:|
| As tested: 50 L crates, lab-pack chemicals, freezer charging, bank debt | 587 | |
| + bulk chemicals | 496 | −91 |
| + 500 L bins instead of crates | 315 | −180 |
| + one PCM-lined truck body instead of bins | 202 | −114 |
| + concessional naira debt | 191 | −11 |
| + 25% capital grant | 180 | −11 |
| + fix supercooling (charge in the pre-cooler, no freezer) | 180 | 0 |
| + fix phase separation (~190 J/g) | 176 | −4 |
| *Refrigerated truck with the same pre-cooling* | *241* | |
| *Open baskets, no cooling* | *80* | |

- **System design** (sourcing and container scale) is worth about ₦385/kg.
- **Financing** is worth about ₦22/kg.
- **At truck scale, the two chemistry problems barely move cost.** They still matter for reliability over many cycles, and for small formats where PCM is a large share of the weight: crates for last-mile delivery, and body-worn cooling packs.

**4. The shipper's case is seasonal.**
- If cooling cuts losses by 10 percentage points, it saves the shipper about ₦35/kg when tomatoes are in glut, ₦100/kg on average, and ₦240/kg in scarcity.
- The PCM truck's premium over open baskets is about ₦122/kg on bank debt and ₦96/kg with every fix. A refrigerated truck's is about ₦161/kg.
- So it pays in scarcity months, is roughly even in average months, and doesn't pay in a glut.
- Off-season use of the same trucks (other produce, or controlled-room-temperature goods) is the next question to model.

**5. Sensitivity** (PCM truck vs refrigerated truck, ₦/kg):

| Change | PCM truck | Refrigerated truck |
|---|---:|---:|
| Base case | 202 | 243 |
| Body conversion cost ₦15M / ₦60M | 189 / 214 | 243 |
| Hub size 1.5 / 18.7 t a day | 214 / 173 | 258 / 231 |
| Trip 30 / 60 h | 199 / 207 | 243 |
| Refrigerated truck at 1.5× / 2.5× normal haulage | 202 | 190 / 297 |
| Mean road temperature 27 / 33 °C | 201 / 203 | 243 |

- The refrigerated-truck price is the assumption that decides the comparison.
- The ~2× figure comes from a 2017 Kaduna–Lagos shipment, so a current quote is the first thing to collect.
- A bigger hub, dispatching one truck a day, cuts cost the most.

**6. Short routes are different.** On a 10-hour Oyo/Ogun → Lagos run, the PCM truck costs about ₦130/kg against about ₦116/kg for a refrigerated truck. It only matches the refrigerated truck with concessional debt and a grant (₦111/kg).

**7. Cheap dollar debt is not cheap in naira.**
- A 7% USD loan costs about 18% in naira if the naira falls 10% a year.
- In a devaluation year, it costs about 39%.
- Only naira-denominated or currency-hedged concessional finance lowers cost.

## Other uses: body-worn cooling

A 15 °C melting point matches commercial PCM cooling vests. One vest uses PCM held at about 15 °C, lasts up to 2.5 hours at 38 °C, and recharges in ice water ([Unitech](https://www.unitechus.com/unitechs-nucool-vest/)). A study of PCM vests at 24 °C and 28 °C recommended testing lower melting points such as 15 °C ([Gao et al., 2011](https://www.lunduniversity.lu.se/lup/publication/8f86ac95-20be-4209-a5a8-6d0864cb2f6d)).

For this PCM, the chemistry matters more in a vest than on a truck:
- It supercools to about 0.8 °C, so ice-water recharging may not reliably make it crystallise.
- Small packs feel phase separation and weight directly.
- Packs worn against skin need robust encapsulation.

## Run it

```
pip install numpy
python model.py
```

All inputs are in the `A` dictionary at the top of `model.py`, and both routes are in `A["routes"]`. Change an input and re-run. `results.txt` holds the output of this version.

## Where the inputs come from

| Tag | Meaning | Examples |
|---|---|---|
| `[thesis]` | Measured in my thesis | Melting enthalpy 87 J/g (85–89, standard T-history method); melting at 15.3 °C; supercooling to 0.8 °C; formulation |
| `[quote]` | Lagos supplier prices I collected, October 2026 | Na₂SO₄ ₦5,000/kg; NaCl ₦9,000 per 500 g; NH₄Cl ₦13,000 per 500 g; borax ₦70,000 per 25 kg; CMC ₦140,000 per 25 kg |
| `[market]` | Published data | Trailer load north→south about ₦2M (May 2026); refrigerated shipment Kaduna→Lagos: 933 × 20 kg crates, about 2 days, 12–14 °C, about 2× normal haulage cost (2017); bank prime rates 25.5–31%; inflation 14.63% (Sept 2026); tomato prices; Nigeria Tax Act 2025 |
| `[est]` | My estimate, to be replaced with a real quote | Truck body conversion, pre-cooler and freezer costs, container prices, trip time, road temperature, loss reduction from cooling |

## Limitations

- Annual time steps; no working capital and no seasonal demand.
- The thermal model is a lumped energy balance with a 10% margin, not a transient simulation of temperature inside the load.
- Produce per truck is capped at the refrigerated-truck load. Axle limits and loading practice may differ.
- Freight is the market hire rate. The PCM truck is assumed to hire at the same rate as an open trailer.
- WACC uses a fixed 60/40 debt-to-equity mix, and the currency effect is approximated. Tax is simplified.
- The latent heat comes from one T-history heating run. DSC would firm it up.

## Sources for market inputs

- Transport losses by packaging: [Onu et al., CIGR Journal, 2021](https://cigrjournal.org/index.php/Ejounral/article/view/6925)
- Trailer cost and basket prices: [Food Business MEA, May 2026](https://www.foodbusinessmea.com/nigerian-tomato-prices-triple-as-supply-shortages-transport-costs-drive-basket-price-to-us78/)
- Refrigerated tomato shipment Kaduna → Lagos: [BusinessDay, 2017](https://businessday.ng/exclusives/article/first-refrigerated-tomato-shipment-arrives-lagos-from-north/)
- Lending rates: [Nairametrics, June 2026](https://nairametrics.com/2026/06/20/nigerian-bank-lending-rates-how-gtbank-zenith-access-compare-in-june-2026/); policy rate: [Arise, Sept 2026](https://www.arise.tv/cbn-cuts-mpr-to-23-from-26-5-as-mpc-revises-policy/)
- Inflation: [Legit.ng, Oct 2026](https://www.legit.ng/business-economy/economy/1736354-good-news-nigerians-september-inflation-rate-drops-1463-food-prices-fall/)
- Exchange rate: [TechEconomy, Oct 2026](https://techeconomy.ng/dollar-to-naira-exchange-rate-today-october-14-2026)
- Tomato price swings: [Gazette, Jan 2025](https://gazettengr.com/price-of-tomatoes-crashes-amid-glut-post-harvest-losses/)
- Tax: [Guardian Nigeria explainer](https://guardian.ng/news/explainer-who-will-pay-under-nigerias-new-tax-laws/)
- PCM cooling vests: [Unitech NuCool](https://www.unitechus.com/unitechs-nucool-vest/); [Gao, Kuklane & Holmér, 2011](https://www.lunduniversity.lu.se/lup/publication/8f86ac95-20be-4209-a5a8-6d0864cb2f6d)
