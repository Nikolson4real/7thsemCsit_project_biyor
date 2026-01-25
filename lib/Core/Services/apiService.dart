import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiClient {
  static const String _baseUrl =
      "http://136.112.79.163:8000/api/v1/game/initial_rule_modified";

  Future<Map<String, dynamic>> fetchRules({
    required int biyoLength,
    required int dandiLength,
    required int fieldLength,
    required int fieldWidth,
    required String surfaceType,
    required int players,
  }) async {
    final body = {
      "game_config": {
        "equipment_dimensions": {
          "biyo_length_cm": biyoLength,
          "dandi_length_cm": dandiLength,
        },
        "ground_description": {
          "field_length_m": fieldLength,
          "field_width_m": fieldWidth,
          "surface_type": surfaceType,
        },
        "num_players_available": players
      },
      "session_id": "game_001"
    };

    final response = await http.post(
      Uri.parse(_baseUrl),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode(body),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception("Failed to load rules");
    }
  }
}
