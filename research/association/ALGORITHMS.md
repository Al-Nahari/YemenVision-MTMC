# Association algorithms and decision protocol

| Method | Implementation path | Complexity | Use / limitation |
|---|---|---:|---|
| cosine baseline | appearance retrieval only | O(NM) | diagnostic only; no probability/decision |
| threshold matching | calibrated score + abstention | O(NM) | permits many-to-many conflicts |
| Hungarian / bipartite | `AssociationEngine.match` | O(n³) | one-to-one within an authorized window |
| graph matching | experimental future path | depends on graph | useful for multi-hop consistency, needs labelled validation |
| probabilistic fusion | calibrated classifier hook | O(NM) | preferred after independent calibration |
| GNN | experimental future path | training/inference dependent | forbidden before sufficient labelled topology data |

Candidate filters are conservative: no authorized topology path, uncalibrated travel range (by default), invalid travel time, clear type conflict, or poor visual quality stops association. Attributes and direction are optional. No rule learns geography or travel time from assumptions.
