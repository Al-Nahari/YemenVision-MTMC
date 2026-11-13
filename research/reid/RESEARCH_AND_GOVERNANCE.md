# ReID research, availability, and governance

| Baseline | Role | Code/weights status | License action |
|---|---|---|---|
| CNN (ResNet) | required reproducible baseline | implemented locally via torchvision | verify torchvision/weight terms before release |
| TransReID | transformer supervised baseline | external repository/weights require pinning | verify repository + checkpoint separately |
| PVEN | view-aware vehicle baseline | public research repository exists | inspect code and checkpoint license before use |
| VehicleNet | multi-source vehicle baseline | paper/dataset provenance needed | do not download or use until license verified |
| ViT ReID | architecture ablation | use an approved implementation | pin commit and license |
| DINOv2 | experimental frozen feature extractor | official code/weights stated Apache-2.0 | pin revision and SHA-256 before use |

The official DINOv2 repository says its code and model weights are Apache-2.0; PVEN has a public repository and paper, but neither fact substitutes for a release-specific review. Do not import external weights into this repository until data owner, security, and license review is complete.

## Attributes

Vehicle type, color, body style, viewpoint, and accessories are optional auxiliary labels. Missing/unclear values remain `unknown`; downstream code must never force a predicted attribute into evidence or use it as an identity assertion.
