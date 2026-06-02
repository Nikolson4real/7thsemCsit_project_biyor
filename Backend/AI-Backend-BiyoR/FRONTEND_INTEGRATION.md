# Frontend Integration Guide - BiyoR AI Rules Engine

## Overview

This document provides comprehensive instructions for integrating the BiyoR AI Rules Engine backend with the Flutter frontend. The backend provides a multi-phase game flow API that supports the complete Dandi Biyo AR gaming experience.

### Architecture Overview

The backend uses a **multi-phase game flow** architecture:

1. **Pre-Game Configuration**: Set equipment and field settings (unchangeable during game)
2. **Initial Briefing**: Get essential rules and AR field layout before starting
3. **Gameplay**: Real-time scoring, rules clarification, and foul checking
4. **Session Management**: Track game sessions across all phases

---

## Backend Setup

### Base URL

```
Development: http://localhost:8000
Production: https://your-production-domain.com
```

### API Version

All endpoints use API version `v1`:
```
/api/v1/game/*
/api/v1/rules/*
```

### Authentication

Currently no authentication is required (add if needed in production).

---

## Multi-Phase Game Flow

### Phase 0: Pre-Game Configuration

Before starting the game, the frontend must collect and configure game settings. **These settings remain constant throughout the game session.**

#### Game Configuration Object

This object is used in **all subsequent API calls**:

```dart
class GameConfiguration {
  final EquipmentDimensions equipmentDimensions;
  final GroundDescription groundDescription;
  final int numPlayersAvailable;
  final int? teamAPlayers;
  final int? teamBPlayers;
  final String languagePreference; // ISO 639-1 code (e.g., "en", "ne")
  
  GameConfiguration({
    required this.equipmentDimensions,
    required this.groundDescription,
    required this.numPlayersAvailable,
    this.teamAPlayers,
    this.teamBPlayers,
    this.languagePreference = "en",
  });
  
  Map<String, dynamic> toJson() => {
    'equipment_dimensions': equipmentDimensions.toJson(),
    'ground_description': groundDescription.toJson(),
    'num_players_available': numPlayersAvailable,
    'team_a_players': teamAPlayers,
    'team_b_players': teamBPlayers,
    'language_preference': languagePreference,
  };
}

class EquipmentDimensions {
  final double dandiLengthCm;
  final double biyoLengthCm;
  final double? biyoDiameterCm;
  
  EquipmentDimensions({
    required this.dandiLengthCm,
    required this.biyoLengthCm,
    this.biyoDiameterCm,
  });
  
  Map<String, dynamic> toJson() => {
    'dandi_length_cm': dandiLengthCm,
    'biyo_length_cm': biyoLengthCm,
    'biyo_diameter_cm': biyoDiameterCm,
  };
}

class GroundDescription {
  final String surfaceType; // "grass", "dirt", "concrete", "sand", "other"
  final double? fieldLengthM;
  final double? fieldWidthM;
  final String? anchorPosition;
  final String? freeTextDescription;
  
  GroundDescription({
    required this.surfaceType,
    this.fieldLengthM,
    this.fieldWidthM,
    this.anchorPosition,
    this.freeTextDescription,
  });
  
  Map<String, dynamic> toJson() => {
    'surface_type': surfaceType,
    'field_length_m': fieldLengthM,
    'field_width_m': fieldWidthM,
    'anchor_position': anchorPosition,
    'free_text_description': freeTextDescription,
  };
}
```

---

### Phase 1: Initial Briefing

**Endpoint**: `POST /api/v1/game/briefing`

**Purpose**: Get essential rules and AR field layout information before the game starts.

#### Request

```dart
class InitialBriefingRequest {
  final GameConfiguration gameConfig;
  final String? sessionId;
  final String? clientVersion;
  
  InitialBriefingRequest({
    required this.gameConfig,
    this.sessionId,
    this.clientVersion,
  });
  
  Map<String, dynamic> toJson() => {
    'game_config': gameConfig.toJson(),
    'session_id': sessionId,
    'client_version': clientVersion,
  };
}
```

#### Response

```dart
class InitialBriefingResponse {
  final List<InstructionCard> importantRules;
  final ARFieldLayout fieldLayout;
  final String gameOverview;
  final ModelMetadata modelMetadata;
  final String? sessionId;
  
  InitialBriefingResponse.fromJson(Map<String, dynamic> json) :
    importantRules = (json['important_rules'] as List)
      .map((card) => InstructionCard.fromJson(card))
      .toList(),
    fieldLayout = ARFieldLayout.fromJson(json['field_layout']),
    gameOverview = json['game_overview'],
    modelMetadata = ModelMetadata.fromJson(json['model_metadata']),
    sessionId = json['session_id'];
}

class ARFieldLayout {
  final String anchorPosition;
  final String? fieldBoundaries;
  final double? safeZoneRadiusM;
  final List<ScoringZone>? scoringZones;
  final String? visualHints;
  
  ARFieldLayout.fromJson(Map<String, dynamic> json) :
    anchorPosition = json['anchor_position'],
    fieldBoundaries = json['field_boundaries'],
    safeZoneRadiusM = json['safe_zone_radius_m']?.toDouble(),
    scoringZones = json['scoring_zones'] != null
      ? (json['scoring_zones'] as List)
        .map((zone) => ScoringZone.fromJson(zone))
        .toList()
      : null,
    visualHints = json['visual_hints'];
}

class ScoringZone {
  final double minDistanceM;
  final double maxDistanceM;
  final int points;
  
  ScoringZone.fromJson(Map<String, dynamic> json) :
    minDistanceM = json['min_distance_m'].toDouble(),
    maxDistanceM = json['max_distance_m'].toDouble(),
    points = json['points'];
}
```

#### Example Usage

```dart
Future<InitialBriefingResponse> getInitialBriefing(GameConfiguration config) async {
  final request = InitialBriefingRequest(
    gameConfig: config,
    sessionId: 'session_${DateTime.now().millisecondsSinceEpoch}',
    clientVersion: '1.0.0',
  );
  
  final response = await http.post(
    Uri.parse('$baseUrl/api/v1/game/briefing'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode(request.toJson()),
  );
  
  if (response.statusCode == 200) {
    return InitialBriefingResponse.fromJson(jsonDecode(response.body));
  } else {
    throw Exception('Failed to get initial briefing: ${response.body}');
  }
}
```

#### UI Implementation Notes

1. **Display Important Rules**: Show 3-5 most critical rules as cards before gameplay
2. **Render AR Field Layout**: Use `fieldLayout` data to dynamically render:
   - Anchor position marker
   - Field boundaries
   - Safe zone circle (radius from `safeZoneRadiusM`)
   - Scoring zone rings (use `scoringZones` data)
3. **Show Game Overview**: Display `gameOverview` text as introduction

---

### Phase 2: Scoring Calculation

**Endpoint**: `POST /api/v1/game/score`

**Purpose**: Calculate score based on estimated distance from anchor.

#### Request

```dart
class ScoringRequest {
  final GameConfiguration gameConfig;
  final double estimatedDistanceM;
  final String? attemptDescription;
  final String? sessionId;
  
  ScoringRequest({
    required this.gameConfig,
    required this.estimatedDistanceM,
    this.attemptDescription,
    this.sessionId,
  });
  
  Map<String, dynamic> toJson() => {
    'game_config': gameConfig.toJson(),
    'estimated_distance_m': estimatedDistanceM,
    'attempt_description': attemptDescription,
    'session_id': sessionId,
  };
}
```

#### Response

```dart
class ScoringResponse {
  final int score;
  final InstructionCard scoringExplanation;
  final bool isValidAttempt;
  final List<InstructionCard>? additionalInfo;
  final ModelMetadata modelMetadata;
  final String? sessionId;
  
  ScoringResponse.fromJson(Map<String, dynamic> json) :
    score = json['score'],
    scoringExplanation = InstructionCard.fromJson(json['scoring_explanation']),
    isValidAttempt = json['is_valid_attempt'],
    additionalInfo = json['additional_info'] != null
      ? (json['additional_info'] as List)
        .map((card) => InstructionCard.fromJson(card))
        .toList()
      : null,
    modelMetadata = ModelMetadata.fromJson(json['model_metadata']),
    sessionId = json['session_id'];
}
```

#### Example Usage

```dart
Future<ScoringResponse> calculateScore(
  GameConfiguration config,
  double distance,
  String description,
) async {
  final request = ScoringRequest(
    gameConfig: config,
    estimatedDistanceM: distance,
    attemptDescription: description,
    sessionId: 'scoring_${DateTime.now().millisecondsSinceEpoch}',
  );
  
  final response = await http.post(
    Uri.parse('$baseUrl/api/v1/game/score'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode(request.toJson()),
  );
  
  if (response.statusCode == 200) {
    return ScoringResponse.fromJson(jsonDecode(response.body));
  } else {
    throw Exception('Failed to calculate score: ${response.body}');
  }
}
```

#### UI Implementation Notes

1. **Distance Estimation**: Use AR to measure distance from anchor to Biyo
2. **Display Score**: Show `score` prominently with animation
3. **Validity Check**: If `isValidAttempt` is false, show warning
4. **Explanation Card**: Display `scoringExplanation` to explain how score was calculated
5. **Additional Info**: Show `additionalInfo` cards if present (warnings, tips)

---

### Phase 3: Rules Clarification

**Endpoint**: `POST /api/v1/game/clarify`

**Purpose**: Answer confusing rules questions during gameplay.

#### Request

```dart
class RulesClarificationRequest {
  final GameConfiguration gameConfig;
  final String question;
  final String? currentSituation;
  final String? sessionId;
  
  RulesClarificationRequest({
    required this.gameConfig,
    required this.question,
    this.currentSituation,
    this.sessionId,
  });
  
  Map<String, dynamic> toJson() => {
    'game_config': gameConfig.toJson(),
    'question': question,
    'current_situation': currentSituation,
    'session_id': sessionId,
  };
}
```

#### Response

```dart
class RulesClarificationResponse {
  final List<InstructionCard> answerCards;
  final String quickAnswer;
  final List<InstructionCard>? relatedRules;
  final ModelMetadata modelMetadata;
  final String? sessionId;
  
  RulesClarificationResponse.fromJson(Map<String, dynamic> json) :
    answerCards = (json['answer_cards'] as List)
      .map((card) => InstructionCard.fromJson(card))
      .toList(),
    quickAnswer = json['quick_answer'],
    relatedRules = json['related_rules'] != null
      ? (json['related_rules'] as List)
        .map((card) => InstructionCard.fromJson(card))
        .toList()
      : null,
    modelMetadata = ModelMetadata.fromJson(json['model_metadata']),
    sessionId = json['session_id'];
}
```

#### Example Usage

```dart
Future<RulesClarificationResponse> clarifyRule(
  GameConfiguration config,
  String question,
  String situation,
) async {
  final request = RulesClarificationRequest(
    gameConfig: config,
    question: question,
    currentSituation: situation,
    sessionId: 'clarify_${DateTime.now().millisecondsSinceEpoch}',
  );
  
  final response = await http.post(
    Uri.parse('$baseUrl/api/v1/game/clarify'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode(request.toJson()),
  );
  
  if (response.statusCode == 200) {
    return RulesClarificationResponse.fromJson(jsonDecode(response.body));
  } else {
    throw Exception('Failed to clarify rule: ${response.body}');
  }
}
```

#### UI Implementation Notes

1. **Question Input**: Provide text input or voice input for questions
2. **Quick Answer**: Display `quickAnswer` immediately at top
3. **Detailed Cards**: Show `answerCards` for in-depth explanation
4. **Related Rules**: Optionally show `relatedRules` in expandable section

---

### Phase 4: Foul Check

**Endpoint**: `POST /api/v1/game/check-foul`

**Purpose**: Check if a specific action violates any rules.

#### Request

```dart
class FoulCheckRequest {
  final GameConfiguration gameConfig;
  final String actionDescription;
  final String? playerTeam;
  final String? sessionId;
  
  FoulCheckRequest({
    required this.gameConfig,
    required this.actionDescription,
    this.playerTeam,
    this.sessionId,
  });
  
  Map<String, dynamic> toJson() => {
    'game_config': gameConfig.toJson(),
    'action_description': actionDescription,
    'player_team': playerTeam,
    'session_id': sessionId,
  };
}
```

#### Response

```dart
class FoulCheckResponse {
  final bool isFoul;
  final InstructionCard foulExplanation;
  final String? penaltyDescription;
  final List<InstructionCard>? relatedRules;
  final ModelMetadata modelMetadata;
  final String? sessionId;
  
  FoulCheckResponse.fromJson(Map<String, dynamic> json) :
    isFoul = json['is_foul'],
    foulExplanation = InstructionCard.fromJson(json['foul_explanation']),
    penaltyDescription = json['penalty_description'],
    relatedRules = json['related_rules'] != null
      ? (json['related_rules'] as List)
        .map((card) => InstructionCard.fromJson(card))
        .toList()
      : null,
    modelMetadata = ModelMetadata.fromJson(json['model_metadata']),
    sessionId = json['session_id'];
}
```

#### Example Usage

```dart
Future<FoulCheckResponse> checkFoul(
  GameConfiguration config,
  String action,
  String team,
) async {
  final request = FoulCheckRequest(
    gameConfig: config,
    actionDescription: action,
    playerTeam: team,
    sessionId: 'foul_${DateTime.now().millisecondsSinceEpoch}',
  );
  
  final response = await http.post(
    Uri.parse('$baseUrl/api/v1/game/check-foul'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode(request.toJson()),
  );
  
  if (response.statusCode == 200) {
    return FoulCheckResponse.fromJson(jsonDecode(response.body));
  } else {
    throw Exception('Failed to check foul: ${response.body}');
  }
}
```

#### UI Implementation Notes

1. **Foul Indicator**: Show clear FOUL/LEGAL indicator based on `isFoul`
2. **Explanation**: Display `foulExplanation` card
3. **Penalty**: If `penaltyDescription` exists, show penalty prominently
4. **Related Rules**: Show `relatedRules` for reference

---

## Common Data Models

### InstructionCard

The core data structure for all rules, explanations, and guidance.

```dart
class InstructionCard {
  final String id;
  final String title;
  final String type; // "RULE", "EXPLANATION", "ACTION_STEP", "WARNING", "TIP", "SCORING"
  final int priority; // 1 (highest) to 10 (lowest)
  final String body;
  final String reasoningSummary;
  final List<RuleReference>? relatedRuleRefs;
  final String? suggestedArVisual;
  
  InstructionCard.fromJson(Map<String, dynamic> json) :
    id = json['id'],
    title = json['title'],
    type = json['type'],
    priority = json['priority'],
    body = json['body'],
    reasoningSummary = json['reasoning_summary'],
    relatedRuleRefs = json['related_rule_refs'] != null
      ? (json['related_rule_refs'] as List)
        .map((ref) => RuleReference.fromJson(ref))
        .toList()
      : null,
    suggestedArVisual = json['suggested_ar_visual'];
}

class RuleReference {
  final String source;
  final String section;
  final int? page;
  
  RuleReference.fromJson(Map<String, dynamic> json) :
    source = json['source'],
    section = json['section'],
    page = json['page'];
}
```

### ModelMetadata

Metadata about the AI model's processing.

```dart
class ModelMetadata {
  final String modelName;
  final int retrievedChunkCount;
  final List<double>? retrievalScores;
  final double? processingTimeMs;
  
  ModelMetadata.fromJson(Map<String, dynamic> json) :
    modelName = json['model_name'],
    retrievedChunkCount = json['retrieved_chunk_count'],
    retrievalScores = json['retrieval_scores'] != null
      ? (json['retrieval_scores'] as List)
        .map((score) => score.toDouble())
        .toList()
      : null,
    processingTimeMs = json['processing_time_ms']?.toDouble();
}
```

---

## UI/UX Best Practices

### InstructionCard Display

Cards should be displayed differently based on their `type`:

```dart
Widget buildInstructionCard(InstructionCard card) {
  Color cardColor;
  IconData cardIcon;
  
  switch (card.type) {
    case 'RULE':
      cardColor = Colors.blue;
      cardIcon = Icons.gavel;
      break;
    case 'EXPLANATION':
      cardColor = Colors.green;
      cardIcon = Icons.info;
      break;
    case 'ACTION_STEP':
      cardColor = Colors.orange;
      cardIcon = Icons.play_arrow;
      break;
    case 'WARNING':
      cardColor = Colors.red;
      cardIcon = Icons.warning;
      break;
    case 'TIP':
      cardColor = Colors.purple;
      cardIcon = Icons.lightbulb;
      break;
    case 'SCORING':
      cardColor = Colors.teal;
      cardIcon = Icons.score;
      break;
    default:
      cardColor = Colors.grey;
      cardIcon = Icons.description;
  }
  
  return Card(
    color: cardColor.withOpacity(0.1),
    child: ListTile(
      leading: Icon(cardIcon, color: cardColor),
      title: Text(card.title, style: TextStyle(fontWeight: FontWeight.bold)),
      subtitle: Text(card.body),
      trailing: Text('Priority: ${card.priority}'),
    ),
  );
}
```

### AR Field Rendering

Use `ARFieldLayout` to render the playing field:

```dart
void renderARField(ARFieldLayout layout, ARCameraController arController) {
  // 1. Place anchor marker at center
  placeAnchorMarker(layout.anchorPosition);
  
  // 2. Draw safe zone circle
  if (layout.safeZoneRadiusM != null) {
    drawCircle(
      center: anchorPosition,
      radius: layout.safeZoneRadiusM!,
      color: Colors.yellow.withOpacity(0.3),
    );
  }
  
  // 3. Draw scoring zones
  if (layout.scoringZones != null) {
    for (var zone in layout.scoringZones!) {
      drawScoringRing(
        center: anchorPosition,
        minRadius: zone.minDistanceM,
        maxRadius: zone.maxDistanceM,
        points: zone.points,
        color: getColorForPoints(zone.points),
      );
    }
  }
  
  // 4. Draw field boundaries
  if (layout.fieldBoundaries != null) {
    drawFieldBoundaries(layout.fieldBoundaries!);
  }
}
```

---

## Complete Game Flow Example

```dart
class DandiBiyoGameController {
  final String baseUrl = 'http://localhost:8000';
  late GameConfiguration gameConfig;
  ARFieldLayout? fieldLayout;
  String? currentSessionId;
  
  // Phase 1: Initialize Game
  Future<void> initializeGame({
    required double dandiLength,
    required double biyoLength,
    required String surfaceType,
    required int numPlayers,
  }) async {
    // Create game configuration
    gameConfig = GameConfiguration(
      equipmentDimensions: EquipmentDimensions(
        dandiLengthCm: dandiLength,
        biyoLengthCm: biyoLength,
      ),
      groundDescription: GroundDescription(
        surfaceType: surfaceType,
        fieldLengthM: 30.0,
        fieldWidthM: 20.0,
      ),
      numPlayersAvailable: numPlayers,
    );
    
    // Get initial briefing
    final briefing = await getInitialBriefing(gameConfig);
    
    // Save field layout for AR rendering
    fieldLayout = briefing.fieldLayout;
    currentSessionId = briefing.sessionId;
    
    // Display important rules to players
    showImportantRules(briefing.importantRules);
    
    // Render AR field
    renderARField(briefing.fieldLayout, arController);
  }
  
  // Phase 2: Calculate Score
  Future<int> scoreAttempt(double distance, String description) async {
    final scoring = await calculateScore(gameConfig, distance, description);
    
    if (!scoring.isValidAttempt) {
      showWarning('Invalid attempt!');
    }
    
    showScoringExplanation(scoring.scoringExplanation);
    return scoring.score;
  }
  
  // Phase 3: Ask Question
  Future<void> askQuestion(String question, String situation) async {
    final clarification = await clarifyRule(gameConfig, question, situation);
    
    // Show quick answer first
    showQuickAnswer(clarification.quickAnswer);
    
    // Show detailed cards
    showAnswerCards(clarification.answerCards);
  }
  
  // Phase 4: Check Foul
  Future<bool> checkAction(String action, String team) async {
    final foulCheck = await checkFoul(gameConfig, action, team);
    
    if (foulCheck.isFoul) {
      showFoulWarning(
        foulCheck.foulExplanation,
        foulCheck.penaltyDescription,
      );
    } else {
      showLegalAction(foulCheck.foulExplanation);
    }
    
    return foulCheck.isFoul;
  }
}
```

---

## Error Handling

All endpoints return standard error responses:

```dart
class ErrorResponse {
  final String code;
  final String message;
  final Map<String, dynamic>? details;
  final String? sessionId;
  
  ErrorResponse.fromJson(Map<String, dynamic> json) :
    code = json['error']['code'],
    message = json['error']['message'],
    details = json['error']['details'],
    sessionId = json['session_id'];
}
```

Handle errors gracefully:

```dart
try {
  final response = await http.post(url, body: body);
  
  if (response.statusCode == 200) {
    return SuccessResponse.fromJson(jsonDecode(response.body));
  } else {
    final error = ErrorResponse.fromJson(jsonDecode(response.body));
    throw Exception('API Error: ${error.message}');
  }
} catch (e) {
  // Show user-friendly error message
  showErrorDialog('Failed to connect to backend. Please try again.');
  logger.error('API Error: $e');
}
```

---

## Testing

### Test the Backend

Before integrating, verify the backend is working:

```bash
# Run the test script
python test_game_flow.py
```

This will test all endpoints and verify responses.

### Mock Data for Development

While developing the UI, you can use mock data:

```dart
class MockGameAPI {
  Future<InitialBriefingResponse> getInitialBriefing(GameConfiguration config) async {
    await Future.delayed(Duration(seconds: 1)); // Simulate network delay
    
    return InitialBriefingResponse.fromJson({
      'important_rules': [
        {
          'id': 'rule_1',
          'title': 'Strike the Biyo',
          'type': 'RULE',
          'priority': 1,
          'body': 'The striker must hit the pointed end of the Biyo to make it airborne.',
          'reasoning_summary': 'Basic striking rule from official rulebook section 2.1',
        }
      ],
      'field_layout': {
        'anchor_position': 'center of field',
        'safe_zone_radius_m': 2.0,
        'scoring_zones': [
          {'min_distance_m': 0, 'max_distance_m': 5, 'points': 1},
          {'min_distance_m': 5, 'max_distance_m': 10, 'points': 2},
        ]
      },
      'game_overview': 'Welcome to Dandi Biyo!',
      'model_metadata': {
        'model_name': 'gemini-2.5-flash',
        'retrieved_chunk_count': 5,
        'processing_time_ms': 1234.5,
      }
    });
  }
}
```

---

## Performance Optimization

### Caching

Cache `GameConfiguration` and `ARFieldLayout` to avoid redundant API calls:

```dart
class GameCache {
  GameConfiguration? _config;
  ARFieldLayout? _layout;
  DateTime? _cacheTime;
  
  void cacheGameData(GameConfiguration config, ARFieldLayout layout) {
    _config = config;
    _layout = layout;
    _cacheTime = DateTime.now();
  }
  
  bool isCacheValid() {
    if (_cacheTime == null) return false;
    return DateTime.now().difference(_cacheTime!) < Duration(hours: 1);
  }
}
```

### Request Debouncing

For rules clarification, debounce user input:

```dart
Timer? _debounce;

void onSearchChanged(String query) {
  if (_debounce?.isActive ?? false) _debounce!.cancel();
  
  _debounce = Timer(const Duration(milliseconds: 500), () {
    // Make API call
    clarifyRule(gameConfig, query, currentSituation);
  });
}
```

---

## Production Considerations

1. **HTTPS**: Always use HTTPS in production
2. **API Keys**: If authentication is added, securely store API keys
3. **Rate Limiting**: Handle 429 (Too Many Requests) responses
4. **Timeout**: Set reasonable timeouts (e.g., 30 seconds)
5. **Offline Mode**: Cache previous responses for offline play
6. **Error Logging**: Send error logs to analytics service

---

## Backend Health Check

Always verify backend health before gameplay:

```dart
Future<bool> isBackendHealthy() async {
  try {
    final response = await http.get(
      Uri.parse('$baseUrl/api/v1/rules/health'),
    ).timeout(Duration(seconds: 5));
    
    if (response.statusCode == 200) {
      final health = jsonDecode(response.body);
      return health['status'] == 'healthy' &&
             health['faiss_index_loaded'] == true &&
             health['gemini_api_accessible'] == true;
    }
    return false;
  } catch (e) {
    return false;
  }
}
```

---

## Summary Checklist

- [ ] Implement `GameConfiguration` model with all fields
- [ ] Create API service class with all 4 phase endpoints
- [ ] Implement `InstructionCard` widget with type-based styling
- [ ] Build AR field rendering using `ARFieldLayout` data
- [ ] Add error handling and user-friendly error messages
- [ ] Implement caching for game config and field layout
- [ ] Test with backend using `test_game_flow.py`
- [ ] Add loading indicators for API calls
- [ ] Implement session ID tracking across phases
- [ ] Add offline mode with cached responses
- [ ] Test complete game flow end-to-end

---

## Support

For questions or issues:
- Check backend logs: `docker-compose logs -f backend`
- Test endpoints: `python test_game_flow.py`
- Review API docs: `http://localhost:8000/api/v1/docs`

Happy coding!
