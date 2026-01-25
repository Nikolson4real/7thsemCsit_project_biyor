import 'package:flutter/material.dart';

class CustomTextButton extends StatelessWidget {
  CustomTextButton({
    super.key,
    this.fontSize,
    this.onPressed,
    this.color,
    this.style,
    this.fontWeight,
    this.text,
    this.decoration,
    this.decorationColor,
  });
  final Function()? onPressed;
  TextStyle? style;
  FontWeight? fontWeight;
  String? text;
  double? fontSize;
  Color? color;
  TextDecoration? decoration;
  Color? decorationColor;

  @override
  Widget build(BuildContext context) {
    return TextButton(
      onPressed: onPressed,
      child: Text(
        text!,
        style: TextStyle(
          fontFamily: "Lato",
          fontSize: fontSize,
          fontWeight: fontWeight,
          //color: color,
          color: color ?? Colors.black,
          decoration: decoration,
          decorationColor: decorationColor,
        ),
      ),
    );
  }
}
