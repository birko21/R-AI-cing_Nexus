# Rights and capability matrix

Every operation is checked against the source policy before it can proceed. A denied operation returns an explicit decision and does not fall back to best-effort behavior.

| Capability | Synthetic fixture | Approved licensed source | Unapproved public source | External kill switch/expired retention |
|---|---|---|---|---|
| Store | Allowed when explicitly approved | Allowed only with approved rights | `NOT_ENTITLED` | `NOT_AVAILABLE` |
| Display | Allowed when explicitly approved | Allowed only with approved rights | `NOT_ENTITLED` | `NOT_AVAILABLE` |
| Export | Allowed when explicitly approved | Allowed only with approved rights | `NOT_ENTITLED` | `NOT_AVAILABLE` |
| LLM | `NOT_AVAILABLE` | `NOT_AVAILABLE` until separately approved | `NOT_AVAILABLE` | `NOT_AVAILABLE` |
| Scrape/outbound | `NOT_AVAILABLE` | `NOT_AVAILABLE` until separately approved | `NOT_AVAILABLE` in G0–G3 | `NOT_AVAILABLE` |

`enabled=false` is a source kill switch. A retention deadline is evaluated against UTC now; expired records are unavailable even if the source was previously entitled. `NOT_ENTITLED` means rights are missing; `NOT_AVAILABLE` means the capability is disabled, deferred or expired.
