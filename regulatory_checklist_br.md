# Brazilian Regulatory Touchpoints for Volunteer ADS-B Reception

**Status:** work in progress, companion to the abstract submitted to the 14th OpenSky Symposium 2026.
**Author:** Eliel Felipe Junior, lawyer (OAB/SP) and independent technology contributor.
**Sensor context:** OpenSky sensor serial -1408044782, Franca, Sao Paulo State, Brazil.

## Disclaimer

This document maps regulatory touchpoints that a volunteer ADS-B operator in Brazil should be aware of before installing a receiver, sharing data with international networks, or publishing analyses. It is written from the perspective of a Brazilian-licensed lawyer who also operates a feeder, but it is not legal advice. Operators should consult qualified counsel for specific situations, and the regulatory environment may evolve.

The document is intentionally concise. The goal is to give prospective Brazilian operators and international researchers a single page that explains where the friction points are, not an exhaustive legal treatise.

## Scope

This document applies to Brazilian-domiciled volunteers who operate passive ADS-B and Mode-S receivers contributing to the OpenSky Network or comparable open infrastructures. It focuses on common configurations such as RTL-SDR receivers and ultrafeeder-based stacks running locally on small hardware. It does not cover commercial operators, certified surveillance providers, or any active transmission scenario.

Four institutional touchpoints are relevant.

## 1. ANATEL (National Telecommunications Agency)

ANATEL regulates the use of the radio spectrum in Brazil, including the homologation of radio equipment placed on the Brazilian market.

ADS-B operates at 1090 MHz. Volunteer reception of ADS-B is passive: the receiver listens to broadcasts that aircraft already emit and does not transmit anything back. As of this writing, ANATEL does not, to the author's knowledge, regulate the passive reception of unencrypted aviation broadcasts as a licensed activity. There is no Brazilian framework comparable to a "general radio listener license" required for ADS-B reception.

However, two practical points apply:

The receiver hardware itself should ideally be ANATEL-homologated. Most commercial RTL-SDR dongles and software-defined-radio modules placed on the Brazilian market are sold with or without homologation, and the regulatory expectation is that telecommunications equipment in use in Brazil bears an ANATEL homologation seal. Hobbyist operators frequently use non-homologated dongles imported directly, which is common but technically not aligned with the homologation regime.

Antenna installations should respect general rules on electromagnetic exposure and physical safety, especially in residential buildings where structural and condominium rules may apply.

Recommendation: prefer ANATEL-homologated receivers when feasible, and document the use of imported hardware in informal personal records in case the equipment is ever questioned.

Reference: <https://www.gov.br/anatel/pt-br>

## 2. ANAC (National Civil Aviation Agency)

ANAC regulates civil aviation in Brazil, including aircraft, operators, airports, and airworthiness. ANAC does not, in the typical interpretation, regulate ground-based passive reception of aviation broadcasts. The set of Brazilian Civil Aviation Regulations (RBAC) applies to aircraft and to certified aviation actors, not to private individuals receiving signals from antennas on their rooftops.

The author is not aware of any RBAC, normative instruction, or ANAC resolution that specifically forbids or restricts the reception of ADS-B by volunteers in Brazil. This is consistent with the international pattern: most jurisdictions do not regulate passive reception of unencrypted aviation broadcasts.

Recommendation: no specific compliance action is currently required toward ANAC for a passive receiver. Operators publishing analyses, however, should respect the general posture of avoiding any framing that could suggest unauthorized provision of surveillance services to third parties.

Reference: <https://www.gov.br/anac/pt-br>

## 3. DECEA and Brazilian Airspace Governance

DECEA (Department of Airspace Control), under the Brazilian Air Force (FAB), is responsible for air traffic control and airspace management in Brazil. DECEA does not regulate private listeners, but it does coordinate the operational use of Brazilian airspace and the data flows that support it.

Two implications for volunteer operators:

Receivers near sensitive locations such as military airbases, presidential transport hubs, or restricted airspace may receive transmissions from aircraft whose operations are not intended for public observation. ADS-B is technically broadcast in the clear and there is no encryption to break, but publishing aggregated data that highlights movements of state, military, or sensitive aircraft can raise legitimate concerns. The community norm in OpenSky and similar networks is to anonymize or exclude such aircraft from public visualizations.

Brazilian military aircraft, presidential transport, and law enforcement aircraft often use specific ICAO 24-bit address ranges and call signs. Operators publishing maps or trajectory analyses should review these prefixes before release and consider exclusion.

Recommendation: exclude state and military aircraft from public visualizations by default. When in doubt, treat anonymization as the conservative path.

Reference: <https://www.gov.br/decea/pt-br>

## 4. LGPD (Brazilian General Data Protection Law)

The LGPD (Law 13,709/2018) regulates the processing of personal data in Brazil. ADS-B data does not, in principle, identify natural persons. It identifies aircraft, by ICAO 24-bit address and flight call sign, not their passengers.

Two situations, however, may bring volunteer reception into LGPD scope:

The location of the volunteer sensor itself can identify the operator, who is a natural person. When a sensor is registered in an open network with precise coordinates, and those coordinates point to a residence, the network is publishing geolocation data about the operator. The OpenSky Network already addresses this by allowing operators to obfuscate the published sensor location, and the practice in this repository is to round receiver coordinates to two decimal places in all public outputs.

Aircraft used by general aviation, especially small private aircraft registered to natural persons, may allow indirect identification of the owner or pilot through cross-referencing with public registries (such as the Brazilian Aircraft Registry, RAB). Publishing detailed trajectories of identifiable private aircraft, when combined with other public data, can amount to the processing of personal data in a way that triggers LGPD considerations.

There is also a cross-border dimension. OpenSky Network is a Swiss non-profit, with infrastructure in Europe. Data forwarded from a Brazilian sensor crosses the border to be hosted under European jurisdiction, which engages the LGPD's chapter on international data transfers. For ADS-B, where the data does not identify natural persons in the typical case, this is normally not a high-risk transfer. The framing matters less because the data is intrinsically non-personal in most cases, and more because operators should be aware of where their data is going.

Recommendation: round receiver coordinates in public outputs, exclude aircraft whose identification could lead back to natural persons in sensitive ways, and be aware that the destination of the data flow is a European infrastructure.

References:
<https://www.gov.br/anpd/pt-br>
<https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm>

## Onboarding Checklist

A short practical checklist for prospective Brazilian volunteer operators.

- [ ] Use ANATEL-homologated receiver hardware when feasible.
- [ ] Round receiver coordinates to no more than two decimal places in public outputs.
- [ ] Exclude state, military, and law-enforcement aircraft from public visualizations.
- [ ] Be aware that data forwarded to OpenSky Network crosses to European infrastructure.
- [ ] Avoid publishing detailed trajectories of identifiable private aircraft.
- [ ] Keep local installation aware of building, structural, and condominium rules for antennas.
- [ ] Document equipment provenance and configuration in personal records.

## Notes on Scope and Limitations

This document reflects the regulatory environment in Brazil as understood by the author in May 2026. Brazilian agencies update normative instruments regularly, and the specific application of these touchpoints to volunteer ADS-B reception has not, to the author's knowledge, been the subject of formal administrative or judicial decisions. Where the document states that an agency does not regulate an activity, it reflects the absence of a clear regulatory statement, not an authoritative declaration of legality.

The document is intentionally short. A more complete legal-source review, including comparisons with European frameworks and with practices in other Latin American jurisdictions, is intended as part of a longer JOAS proceedings paper if the abstract is accepted.

## Contributing and Feedback

Comments, corrections, and suggestions are welcome. The document is maintained at:

<https://github.com/eliel9012/opensky-br-franca-coverage>

Contact: through the GitHub repository or via the author's ORCID profile, <https://orcid.org/0000-0002-6333-1187>.
