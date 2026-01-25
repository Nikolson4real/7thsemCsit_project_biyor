import 'package:biyoar/Core/Services/apiService.dart';
import 'package:biyoar/Core/Models/game_rule.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'biyorEvents.dart';
import 'biyorStates.dart';

class GameRulesBloc extends Bloc<BiyorEvents, BiyorStates> {
  final ApiClient apiService;

  GameRulesBloc(this.apiService) : super(GameRulesInitial()) {
    on<FetchGameRules>((event, emit) async {
      emit(GameRulesLoading());

      try {
        final data = await apiService.fetchRules(
          biyoLength: event.biyoLength,
          dandiLength: event.dandiLength,
          fieldLength: event.fieldLength,
          fieldWidth: event.fieldWidth,
          surfaceType: event.surfaceType,
          players: event.players,
        );

        // Parse JSON into typed GameRule objects
        final List<GameRule> rules = (data["rules_cards"] as List)
            .map((json) => GameRule.fromJson(json as Map<String, dynamic>))
            .toList();

        emit(GameRulesLoaded(rules));
      } catch (e) {
        emit(GameRulesError(e.toString()));
      }
    });
  }
}
