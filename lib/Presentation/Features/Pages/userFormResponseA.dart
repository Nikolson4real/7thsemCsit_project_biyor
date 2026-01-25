import 'package:biyoar/Core/Customs/customElevatedButton.dart';
import 'package:biyoar/Core/Customs/customText.dart';
import 'package:biyoar/Core/Customs/customColors.dart';
import 'package:biyoar/test/woodenChickenObject.dart';
import 'package:flutter/material.dart';

class UserFormResponseA extends StatelessWidget {
  final String groundType;

  const UserFormResponseA({
    super.key,
    required this.groundType,
  });

  // Static data based on ground type
  List<Map<String, String>> _getStaticRules() {
    if (groundType.toLowerCase() == 'concrete') {
      return [
        {
          'title': 'Surface Preparation',
          'rule':
              'Ensure the concrete surface is clean and free of debris. Mark the playing boundaries clearly with chalk or tape.',
        },
        {
          'title': 'Safety Precautions',
          'rule':
              'Players should wear appropriate footwear with good grip. Knee and elbow pads are recommended for protection during play.',
        },
        {
          'title': 'Equipment Care',
          'rule':
              'Use equipment designed for hard surfaces. Wooden biyo may wear faster on concrete, consider using reinforced variants.',
        },
        {
          'title': 'Playing Distance',
          'rule':
              'On concrete, the biyo travels farther. Adjust your striking force accordingly and maintain safe distances between players.',
        },
      ];
    } else {
      // Grass
      return [
        {
          'title': 'Ground Based Equipment',
          'rule':
              'Use kneepads or basic protective gear to prevent injuries while playing on hard or uneven ground.',
        },
        {
          'title': 'Marking the Field',
          'rule':
              'Use lime powder or temporary spray paint to mark the boundaries. Ensure lines are visible throughout the game.',
        },
        {
          'title': 'Equipment Handling',
          'rule':
              'On grass, the biyo may bounce unpredictably. Players should position themselves for varied trajectories.',
        },
        {
          'title': 'Player Movement',
          'rule':
              'Wear shoes with cleats or studs for better grip on grass. Avoid sliding tackles to prevent injuries.',
        },
      ];
    }
  }

  @override
  Widget build(BuildContext context) {
    final rules = _getStaticRules();

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
              padding: const EdgeInsets.only(top: 100, bottom: 160),
              child: ListView.builder(
                padding: const EdgeInsets.symmetric(horizontal: 10),
                itemCount: rules.length,
                itemBuilder: (context, index) {
                  final rule = rules[index];
                  final String title = rule['title'] ?? 'Rule ${index + 1}';
                  final String ruleText = rule['rule'] ?? '';

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
                              crossAxisAlignment: CrossAxisAlignment.start,
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
                                    text: title,
                                    fontSize: 18,
                                    color: whiteColor,
                                  ),
                                ),
                              ],
                            ),
                            SizedBox(height: 10),
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
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
                                    text: ruleText,
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

            // Title (fixed at top center)
            Positioned(
              top: 45,
              left: 0,
              right: 0,
              child: Center(
                child: Column(
                  children: [
                    CustomText(
                      text:
                          "Rules for ${groundType[0].toUpperCase()}${groundType.substring(1)}",
                      color: Colors.white,
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                    ),
                  ],
                ),
              ),
            ),

            // Bottom buttons (fixed at bottom)
            Positioned(
              bottom: 30,
              left: 20,
              right: 20,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Go to AR Button
                  CustomButton(
                    color: woodBrown.withOpacity(0.2),
                    borderColor: borderColor,
                    borderWidth: 1,
                    onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => WoodenChickenObjectWidget(),
                        ),
                      );
                    },
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        CustomText(
                          text: "Go to AR",
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: whiteColor,
                        ),
                        SizedBox(width: 10),
                        Icon(Icons.arrow_forward_ios, color: whiteColor),
                      ],
                    ),
                  ),
                  SizedBox(height: 10),
                  // Back to Form Button
                  CustomButton(
                    color: woodBrown.withOpacity(0.2),
                    borderColor: borderColor,
                    borderWidth: 1,
                    onPressed: () {
                      Navigator.pop(context);
                    },
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.arrow_back_ios, color: whiteColor),
                        SizedBox(width: 10),
                        CustomText(
                          text: "Back to Form",
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: whiteColor,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
