import 'dart:async';
import 'dart:math';

import 'package:biyoar/Core/Customs/customColors.dart';
import 'package:biyoar/Presentation/Features/Dashboard/userdash2.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen>
    with TickerProviderStateMixin {
  // Text wave animation
  late AnimationController _textController;

  // Logo drop animation
  late AnimationController _logoController;
  late Animation<double> _logoDropAnimation;

  final String appName = "BiyoR";

  @override
  void initState() {
    super.initState();

    /// Wave text controller
    _textController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat();

    /// Logo drop controller
    _logoController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    );

    _logoDropAnimation = Tween<double>(
      begin: -350, // Start from sky
      end: 0, // Final position
    ).animate(
      CurvedAnimation(
        parent: _logoController,
        curve: Curves.bounceOut, // POP effect
      ),
    );

    _logoController.forward();

    /// Navigate after splash
    Future.delayed(const Duration(seconds: 5), () {
      Navigator.of(context).pushReplacement(
        PageRouteBuilder(
          pageBuilder: (context, animation, secondaryAnimation) =>
              const UserDashboardScreen2(),
          transitionsBuilder: (context, animation, secondaryAnimation, child) {
            return FadeTransition(opacity: animation, child: child);
          },
          transitionDuration: const Duration(milliseconds: 500),
        ),
      );
    });
  }

  @override
  void dispose() {
    _textController.dispose();
    _logoController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;

    return Scaffold(
      body: Container(
        height: size.height,
        width: size.width,
        decoration: const BoxDecoration(
          image: DecorationImage(
            image: AssetImage("assets/images/biyorbgi.jpg"),
            fit: BoxFit.cover,
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            /// LOGO DROP ANIMATION
            AnimatedBuilder(
              animation: _logoDropAnimation,
              builder: (context, child) {
                return Transform.translate(
                  offset: Offset(0, _logoDropAnimation.value),
                  child: child,
                );
              },
              child: Image.asset(
                "assets/images/apicon1.png",
                width: 300,
                height: 300,
              ),
            ),

            const SizedBox(height: 12),

            /// WAVING TEXT
            AnimatedBuilder(
              animation: _textController,
              builder: (context, child) {
                return Row(
                  mainAxisSize: MainAxisSize.min,
                  children: List.generate(appName.length, (index) {
                    double offsetY = sin(
                          (_textController.value * 2 * pi) + (index * 0.5),
                        ) *
                        10;

                    return Transform.translate(
                      offset: Offset(0, -offsetY),
                      child: Text(
                        appName[index],
                        style: GoogleFonts.irishGrover(
                          textStyle: const TextStyle(
                            color: Colors.white,
                            fontSize: 50,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    );
                  }),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}
