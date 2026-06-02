# Dandi Biyo Score Calculation

This document explains the scoring algorithm used in the Text-Based Conversational Referee system.

## Overview

Each turn in Dandi Biyo consists of two phases:
1. **Hutnu** (Hitting) - The batter hits the Dandi with the Biyo
2. **Tyak** (Tapping) - Optional follow-up where the batter taps the Biyo in the air

## Score Formula

```
Turn Score = Hutnu Score + Tyak Score
```

### Hutnu Score Calculation

```
Hutnu Score = Zone Points + Safe Zone Points
```

| Component | Description | Points |
|-----------|-------------|--------|
| **Zone** | Where the Biyo lands (0-6) | 0-6 points |
| **Safe Zone** | Additional bonus for reaching safe areas | See below |

#### Safe Zone Points

| Safe Zone | Points |
|-----------|--------|
| Nearest | +2 |
| Middle | +4 |
| Furthest | +6 |
| None | +0 |

**Example:** Biyo lands in Zone 4, batter reaches middle safe zone
- Hutnu Score = 4 + 4 = **8 points**

### Tyak Score Calculation

```
Tyak Score = 2 × Zone (if valid)
```

**Conditions for valid Tyak:**
- Hutnu was NOT out
- Tyak was attempted
- Tyak was NOT out
- At least 1 tap was made
- Zone ≤ 6 (not boundary)

**Example:** Tyak lands in Zone 5 with 3 taps
- Tyak Score = 2 × 5 = **10 points**

## OUT Conditions

If a player is OUT, they score 0 for that phase:

### Hutnu OUT Conditions
- Biyo caught in air by fielder
- Biyo returns to Khop (starting point)
- Dandi is hit by thrown Biyo
- Boundary violation (Zone > 6)

### Tyak OUT Conditions
- Same as Hutnu conditions
- **Note:** If OUT during Tyak, Hutnu score is preserved

## Complete Turn Examples

### Example 1: Perfect Turn
| Phase | Details | Score |
|-------|---------|-------|
| Hutnu | Zone 5, Furthest safe | 5 + 6 = 11 |
| Tyak | Zone 6, 4 taps | 2 × 6 = 12 |
| **Total** | | **23 points** |

### Example 2: No Tyak Attempt
| Phase | Details | Score |
|-------|---------|-------|
| Hutnu | Zone 3, Middle safe | 3 + 4 = 7 |
| Tyak | Not attempted | 0 |
| **Total** | | **7 points** |

### Example 3: Hutnu OUT
| Phase | Details | Score |
|-------|---------|-------|
| Hutnu | Caught in air | 0 |
| Tyak | N/A (Hutnu was OUT) | 0 |
| **Total** | | **0 points** |

### Example 4: Tyak OUT (Hutnu Preserved)
| Phase | Details | Score |
|-------|---------|-------|
| Hutnu | Zone 4, Nearest safe | 4 + 2 = 6 |
| Tyak | OUT (caught) | 0 |
| **Total** | | **6 points** |

## Game Rules

- **Game Duration:** 30 minutes per team
- **Time Decrement:** ~1 minute per turn
- **Game End:** When time reaches 0

## Code Reference

The scoring algorithm is implemented in:
- `app/chat_referee.py` → `calculate_score()` method
- `app/chat_models.py` → `HutneEvent.score` and `TyakEvent.score` properties

## API Response

Score breakdown is returned in the `embedded_json` field:

```json
{
  "type": "score_breakdown",
  "data": {
    "hutnu_zone": 5,
    "hutnu_safe": "furthest",
    "hutnu_safe_points": 6,
    "hutnu_score": 11,
    "tyak_attempted": true,
    "tyak_zone": 6,
    "tyak_taps": 4,
    "tyak_score": 12,
    "turn_score": 23,
    "is_out": false,
    "out_reason": null,
    "reasoning": "Hutnu: zone 5 + safe 'furthest' (6) = 11 | Tyak: 2 × zone 6 = 12 (4 taps) | TOTAL: 11 + 12 = 23"
  }
}
```
