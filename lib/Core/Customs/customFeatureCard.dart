import 'package:biyoar/Core/Customs/customText.dart';
import 'package:flutter/material.dart';

class CustomCards extends StatelessWidget {
  final String? imagePath; // Existing image path
  final Widget? customImage; // Existing custom widget
  final IconData? icon; // NEW: optional icon to display
  final double? iconSize; // optional size for the icon
  final Color? iconColor; // optional color for the icon

  CustomCards({
    Key? key,
    this.imagePath,
    this.customImage,
    this.icon, // NEW
    this.iconSize,
    this.iconColor,
    this.fontSize,
    this.cardcolor,
    this.decorationColor,
    this.style,
    this.fontWeight,
    this.fontFamily,
    this.text,
    this.borderColor,
    this.decoration,
    this.border,
    this.child,
    this.splitOnSpace = false,
  }) : super(key: key);

  TextStyle? style;
  FontWeight? fontWeight;
  String? text;
  double? fontSize;
  Color? cardcolor;
  Color? borderColor;
  String? fontFamily;
  TextDecoration? decoration;
  Color? decorationColor;
  BoxBorder? border;
  final bool splitOnSpace;
  final Widget? child;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      child: Container(
        height: MediaQuery.of(context).size.height * 0.15,
        width: MediaQuery.of(context).size.width * 0.22,
        decoration: BoxDecoration(
          color: cardcolor ?? Colors.white,
          border: border,
          borderRadius: BorderRadius.circular(15),
          boxShadow: [BoxShadow(color: Colors.grey.withOpacity(1))],
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            SizedBox(
              height: 70,
              width: 50,
              child: customImage != null
                  ? customImage
                  : (icon != null
                      ? Icon(
                          icon,
                          size: iconSize ?? 40,
                          color: iconColor ?? Colors.black,
                        )
                      : (imagePath != null
                          ? Image.asset(imagePath!, fit: BoxFit.cover)
                          : Container())),
            ),
            const SizedBox(height: 5),
            CustomText(
              text: text ?? "",
              fontFamily: fontFamily,
              maxLength: 20,
              textAlign: TextAlign.center,
              splitOnSpace: splitOnSpace,
              fontSize: fontSize,
              fontWeight: fontWeight,
              color: Colors.white,
              decoration: decoration,
              decorationColor: decorationColor,
            ),
          ],
        ),
      ),
    );
  }
}
