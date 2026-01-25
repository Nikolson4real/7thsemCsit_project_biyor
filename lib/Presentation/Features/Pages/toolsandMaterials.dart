import 'package:biyoar/Core/Customs/customColors.dart';
import 'package:biyoar/Core/Customs/customText.dart';
import 'package:flutter/material.dart';

class ToolsMaterialsPage extends StatefulWidget {
  const ToolsMaterialsPage({super.key});

  @override
  State<ToolsMaterialsPage> createState() => _ToolsMaterialsPageState();
}

class _ToolsMaterialsPageState extends State<ToolsMaterialsPage> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(65),
        child: ClipRRect(
          borderRadius: const BorderRadius.only(
            bottomLeft: Radius.circular(20),
            bottomRight: Radius.circular(20),
          ),
          child: AppBar(
            centerTitle: true,
            title: const CustomText(
              text: 'Tools & Materials',
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: whiteColor,
            ),
            backgroundColor: Colors.transparent,
            elevation: 0,
            flexibleSpace: Container(
              decoration: const BoxDecoration(
                image: DecorationImage(
                  image: AssetImage("assets/images/biyorbgi.jpg"),
                  fit: BoxFit.cover,
                ),
              ),
            ),
            leading: IconButton(
              icon: const Icon(Icons.arrow_back, color: whiteColor, size: 30),
              onPressed: () => Navigator.pop(context),
            ),
          ),
        ),
      ),
      backgroundColor: whiteColor,
      body: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        SizedBox(height: 10),
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.only(
              right: 20,
              left: 20,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Heading
                buildHeading("Dandi"),
                buildBullet("Length: 45 cm"),
                buildBullet(
                    "Material: Sturdy wood suitable for hitting the Biyo"),
                buildBullet(
                    "Purpose: Used by the hitter to strike the Biyo and send it flying"),

                const SizedBox(height: 20),

                buildHeading("Biyo"),
                buildBullet("Length: 15 cm"),
                buildBullet("Material: Lightweight wood"),
                buildBullet(
                    "Purpose: The target stick to be hit; distance determines Landing Zone score"),

                const SizedBox(height: 20),

                buildHeading("Playing Area"),
                buildBullet(
                    "Size: ~10 m field length, central square with connecting paths and fan-shaped landing zones"),
                buildBullet("Surface: Flat ground or grass"),
                buildBullet(
                    "Purpose: Provides sufficient space for safe Hutnu and Tyak play"),

                const SizedBox(height: 20),

                buildHeading("Markers"),
                buildBullet(
                    "Starting Point: Khop location for placing the Biyo"),
                buildBullet(
                    "Scoring Zones: Fan-shaped landing zones (Zone 0–6) and Safe Zones (1–3 on each path)"),
                buildBullet("Boundaries: Outside Zone 6 counts as OUT"),

                const SizedBox(height: 20),

                buildHeading("Measuring Tool"),
                buildBullet("Optional: Ruler or tape (for traditional play)"),

                const SizedBox(height: 20),

                buildHeading("Players"),
                buildBullet("Minimum: 5 players (For each team)"),
                buildBullet("Team Size: 5 active players, 2 substitutes"),
              ],
            ),
          ),
        ),
      ]),
    );
  }

  /// **************CUSTOM HEADING WIDGET *******************
  Widget buildHeading(String text) {
    return Text(
      text,
      style: const TextStyle(
        fontSize: 20,
        fontWeight: FontWeight.bold,
      ),
    );
  }

  /// **************CUSTOM HEADING WIDGET *******************

  /// **************CUSTOM BULLET POINT WIDGET ********************************
  Widget buildBullet(String text) {
    return Padding(
      padding: const EdgeInsets.only(left: 8, top: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text("•  ", style: TextStyle(fontSize: 16)),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(fontSize: 16, height: 1.4),
            ),
          )
        ],
      ),
    );
  }

  /// **************CUSTOM BULLET POINT WIDGET ********************************
}
