/// Model class representing a game rule from the API
class GameRule {
  final String cardId;
  final String category;
  final String title;
  final String body;
  final int priority;
  final String iconHint;
  final String arHighlight;

  GameRule({
    required this.cardId,
    required this.category,
    required this.title,
    required this.body,
    required this.priority,
    required this.iconHint,
    required this.arHighlight,
  });

  /// Factory constructor to create a GameRule from JSON
  factory GameRule.fromJson(Map<String, dynamic> json) {
    return GameRule(
      cardId: json['card_id']?.toString() ?? '',
      category: json['category']?.toString() ?? '',
      title: json['title']?.toString() ?? '',
      body: json['body']?.toString() ?? '',
      priority: json['priority'] is int ? json['priority'] : 0,
      iconHint: json['icon_hint']?.toString() ?? '',
      arHighlight: json['ar_highlight']?.toString() ?? '',
    );
  }

  /// Convert the GameRule to a JSON map
  Map<String, dynamic> toJson() {
    return {
      'card_id': cardId,
      'category': category,
      'title': title,
      'body': body,
      'priority': priority,
      'icon_hint': iconHint,
      'ar_highlight': arHighlight,
    };
  }

  @override
  String toString() {
    return 'GameRule(cardId: $cardId, category: $category, title: $title)';
  }
}
