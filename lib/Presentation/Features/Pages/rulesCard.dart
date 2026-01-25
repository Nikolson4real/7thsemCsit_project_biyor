import 'package:biyoar/Core/Customs/customElevatedButton.dart';
import 'package:biyoar/Core/Customs/customText.dart';
import 'package:biyoar/Core/Models/game_rule.dart';
import 'package:biyoar/test/woodenChickenObject.dart';
import 'package:flutter/material.dart';

import 'package:biyoar/Core/Customs/customColors.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:biyoar/Core/StateManagement/biyorStates.dart';
import 'package:biyoar/Core/StateManagement/gameRulesBloc.dart';

class RulesCardBiyor extends StatefulWidget {
  const RulesCardBiyor({super.key});

  @override
  State<RulesCardBiyor> createState() => _RulesCardBiyorState();
}

class _RulesCardBiyorState extends State<RulesCardBiyor> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        height: double.infinity,
        width: double.infinity,
        decoration: BoxDecoration(
          image: DecorationImage(
            image: AssetImage("assets/images/biyorbgi.jpg"),
            fit: BoxFit.cover,
          ),
        ),
        child: Stack(
          children: [
            // Scrollable content
            Padding(
              padding: const EdgeInsets.only(top: 100, bottom: 100),
              child: BlocBuilder<GameRulesBloc, BiyorStates>(
                builder: (context, state) {
                  if (state is GameRulesLoading) {
                    return Center(
                        child: CircularProgressIndicator(color: borderColor));
                  } else if (state is GameRulesError) {
                    return Center(
                        child: CustomText(
                            text: state.message, color: Colors.white));
                  } else if (state is GameRulesLoaded) {
                    if (state.rules.isEmpty) {
                      return Center(
                          child: CustomText(
                              text: "No rules found for this configuration.",
                              color: Colors.white));
                    }
                    return ListView.builder(
                      padding: const EdgeInsets.symmetric(horizontal: 1),
                      itemCount: state.rules.length,
                      itemBuilder: (context, index) {
                        final GameRule rule = state.rules[index];
                        final String title = rule.title.isNotEmpty
                            ? rule.title
                            : (rule.category.isNotEmpty
                                ? rule.category
                                : 'Rule ${index + 1}');
                        final String ruleText = rule.body;

                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 5),
                          child: Card(
                            color: woodBrown.withOpacity(0.4),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(15),
                              side: BorderSide(color: borderColor, width: 2),
                            ),
                            child: Padding(
                              padding: const EdgeInsets.all(15),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      CustomText(
                                        text: "Title:",
                                        color: whiteColor,
                                        fontSize: 18,
                                        fontWeight: FontWeight.bold,
                                      ),
                                      SizedBox(width: 10),
                                      Expanded(
                                        child: CustomText(
                                          text: title.toString(),
                                          fontSize: 18,
                                          color: whiteColor,
                                        ),
                                      ),
                                    ],
                                  ),
                                  SizedBox(height: 10),
                                  Row(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      CustomText(
                                        color: whiteColor,
                                        text: "Rule:",
                                        overflow: TextOverflow.ellipsis,
                                        textAlign: TextAlign.left,
                                        fontSize: 18,
                                        fontWeight: FontWeight.bold,
                                      ),
                                      SizedBox(width: 10),
                                      Expanded(
                                        child: CustomText(
                                          text: ruleText.toString(),
                                          color: whiteColor,
                                          fontSize: 16,
                                          overflow: TextOverflow.visible,
                                        ),
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                          ),
                        );
                      },
                    );
                  }
                  return Center(
                      child: CustomText(
                          text: "No data loaded.", color: Colors.white));
                },
              ),
            ),

            // Back button (fixed at top left)
            Positioned(
              top: 40,
              left: 10,
              child: IconButton(
                onPressed: () {
                  Navigator.pop(context);
                },
                icon: Icon(Icons.arrow_back),
                color: whiteColor,
                iconSize: 30,
              ),
            ),
            Positioned(
              top: 45, // Adjust top to align nicely with back button
              left: 0,
              right: 0,
              child: Center(
                child: CustomText(
                  text: "Rules Book",
                  color: Colors.white,
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),

            // Bottom button (fixed at bottom)
            Positioned(
              bottom: 30,
              left: 20,
              right: 20,
              child: CustomButton(
                color: woodBrown.withOpacity(0.2),
                borderColor: borderColor,
                borderWidth: 1,
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (_) => WoodenChickenObjectWidget()),
                  );
                },
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    CustomText(
                      text: "Go To AR Screen",
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: whiteColor,
                    ),
                    SizedBox(width: 10),
                    Icon(Icons.arrow_forward_ios, color: whiteColor)
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
