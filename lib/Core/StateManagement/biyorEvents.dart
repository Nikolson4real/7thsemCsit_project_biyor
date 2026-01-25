import 'package:equatable/equatable.dart';

abstract class BiyorEvents extends Equatable {
  const BiyorEvents();
  @override
  List<Object> get props => [];
}

class FetchGameRules extends BiyorEvents {
  final int biyoLength;
  final int dandiLength;
  final int fieldLength;
  final int fieldWidth;
  final String surfaceType;
  final int players;

  FetchGameRules({
    required this.biyoLength,
    required this.dandiLength,
    required this.fieldLength,
    required this.fieldWidth,
    required this.surfaceType,
    required this.players,
  });
}
