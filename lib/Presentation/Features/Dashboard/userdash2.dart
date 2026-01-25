import 'dart:async';

import 'package:biyoar/Core/Customs/customColors.dart';
import 'package:biyoar/Core/Customs/customElevatedButton.dart';
import 'package:biyoar/Core/Customs/customText.dart';
import 'package:biyoar/Presentation/Features/Pages/aboutUs.dart';
import 'package:biyoar/Presentation/Features/Pages/BiyorRuleBook.dart';
import 'package:biyoar/Presentation/Features/Pages/llmform.dart';
import 'package:biyoar/Presentation/Features/Pages/scoreCalculationBiyor.dart';
import 'package:biyoar/Presentation/Features/Pages/toolsandMaterials.dart';
import 'package:biyoar/test/woodenChickenObject.dart';
import 'package:flutter/material.dart';

class UserDashboardScreen2 extends StatefulWidget {
  const UserDashboardScreen2({super.key});

  @override
  State<UserDashboardScreen2> createState() => _UserDashboardScreen2State();
}

class _UserDashboardScreen2State extends State<UserDashboardScreen2> {
  bool showDot = true;

  @override
  void initState() {
    super.initState();
    Timer.periodic(const Duration(milliseconds: 600), (timer) {
      if (!mounted) {
        timer.cancel();
        return;
      }
      setState(() => showDot = !showDot);
    });
  }

  @override
  Widget build(BuildContext context) {
    final h = MediaQuery.of(context).size.height;
    final w = MediaQuery.of(context).size.width;

    final buttonHeight = h * 0.075;

    return Scaffold(
      body: Stack(
        children: [
          // 🔹 Background
          Positioned.fill(
            child: Image.asset(
              "assets/images/biyorbgi.jpg",
              fit: BoxFit.cover,
            ),
          ),

          // 🔹 CENTER CONTENT (unchanged alignment)
          Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              SizedBox(height: h * 0.08),

              const Center(
                child: CustomText(
                  text: "DandiBiyo",
                  fontSize: 30,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),

              Center(
                child: CustomText(
                  text: "Reviving Tradition Through",
                  fontSize: 18,
                  color: Colors.white.withOpacity(0.75),
                ),
              ),
              Center(
                child: CustomText(
                  text: "Augmented Reality",
                  fontSize: 18,
                  color: Colors.white.withOpacity(0.75),
                ),
              ),

              SizedBox(height: h * 0.05),

              // 🟡 ICON PERFECTLY CENTERED
              Center(
                child: Image.asset(
                  "assets/images/apicon1.png",
                  height: 300,
                  width: 300,
                ),
              ),
            ],
          ),

          // 🔹 BOTTOM BUTTON SECTION
          SafeArea(
            child: Align(
              alignment: Alignment.bottomCenter,
              child: Padding(
                padding: EdgeInsets.only(
                  bottom: 60 + MediaQuery.of(context).padding.bottom,
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // 🎯 Start BiyoR
                    SizedBox(
                      height: buttonHeight,
                      width: w * 0.9,
                      child: CustomButton(
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => WoodenChickenObjectWidget(),
                            ),
                          );
                        },
                        color: woodBrown.withOpacity(0.45),
                        borderColor: borderColor,
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(Icons.camera_alt,
                                color: Colors.white, size: 30),
                            const SizedBox(width: 10),
                            SizedBox(
                              width: w * 0.6,
                              child: Center(
                                child: CustomText(
                                  text: "Start BiyoR",
                                  color: Colors.white,
                                  fontSize: 25,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),

                    SizedBox(height: h * 0.035),
                    // 🎯 Start BiyoR
                    SizedBox(
                      height: buttonHeight,
                      width: w * 0.9,
                      child: CustomButton(
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              // builder: (_) => LLMForm(),
                              builder: (_) => BiyoRScoreCalculationLLM(),
                            ),
                          );
                        },
                        color: woodBrown.withOpacity(0.45),
                        borderColor: borderColor,
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(Icons.calculate_outlined,
                                color: Colors.white, size: 30),
                            const SizedBox(width: 10),
                            SizedBox(
                              width: w * 0.6,
                              child: Center(
                                child: CustomText(
                                  text: "Score Calculator",
                                  color: Colors.white,
                                  fontSize: 25,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),

                    SizedBox(height: h * 0.025),

                    const SizedBox(height: 14),

                    // 🔧 Tools / About (unchanged)
                    Padding(
                      padding: const EdgeInsets.only(left: 20, right: 20),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceAround,
                        children: [
                          Column(
                            children: [
                              GestureDetector(
                                onTap: () {
                                  Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (_) =>
                                          const ToolsMaterialsPage(),
                                    ),
                                  );
                                },
                                child: const Icon(Icons.settings,
                                    color: Colors.white, size: 30),
                              ),
                              const CustomText(
                                text: "Tools/Materials",
                                color: Colors.white,
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ],
                          ),
                          Column(
                            children: [
                              GestureDetector(
                                onTap: () {
                                  Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (_) => const BiyorRuleBook(),
                                    ),
                                  );
                                },
                                child: const Icon(Icons.menu_book,
                                    color: Colors.white, size: 30),
                              ),
                              const CustomText(
                                text: "Rule Book",
                                color: Colors.white,
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ],
                          ),
                          Column(
                            children: [
                              GestureDetector(
                                onTap: () {
                                  Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (_) => AboutUsPage(),
                                    ),
                                  );
                                },
                                child: const Icon(Icons.info,
                                    color: Colors.white, size: 30),
                              ),
                              const CustomText(
                                text: "About BiyoR",
                                color: Colors.white,
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
