# legacy/

Superseded modules, kept for reference. **Not imported by the package.**

| File | Superseded by | Notes |
|---|---|---|
| `swing_points.py` | `src/ict/concepts/market_structure.py` (`SwingPointScanner`) | Earlier standalone copy; the canonical scanner lives in the package and was the project's one `detection: implemented` concept. |
| `daily_bias_sniper.py` | `src/ict/models/ict/daily_bias.py` (`DailyBiasModel`) | Earlier sniper draft; nothing imported it. Reconcile any unique logic into the package version, then this file can be deleted. |

These were orphan modules sitting outside the old `ict_library/` package. They are
preserved here rather than deleted so no logic is lost; once you've confirmed the
package versions cover everything, delete this folder.
