import 'package:biyoar/Core/Customs/customColors.dart';
import 'package:flutter/material.dart';

class CustomButton extends StatelessWidget {
  CustomButton({
    Key? key,
    this.color,
    this.disabledColor,
    this.disabledTextColor,
    this.child,
    this.onPressed,
    this.fontWeight,
    this.fontsize,
    this.text,
    this.borderColor, // Add borderColor property for custom border color
    this.borderWidth, // Add borderWidth property for custom border width
    this.leading,
    this.eleIcon,
    this.trailing,
  }) : super(key: key);

  final Function()? onPressed;
  final Color? color;
  final String? text;
  final double? fontsize;
  final FontWeight? fontWeight;
  final Widget? child;
  final Color? borderColor; // Add borderColor property
  final double? borderWidth; // Add borderWidth property
  final Widget? leading; // Add leading icon property
  final Widget? trailing;
  final IconData? eleIcon;
  final Color? disabledColor;
  final Color? disabledTextColor;
  // Add trailing icon property

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(left: 15, right: 15, top: 5),
      child: SizedBox(
        height: MediaQuery.of(context).size.height * 0.06,
        width: MediaQuery.of(context).size.width * 1,
        child: ElevatedButton(
          style: ElevatedButton.styleFrom(
            backgroundColor: color ?? primeColor,
            disabledBackgroundColor:
                disabledColor ?? Colors.grey, // Set the disabled color
            disabledForegroundColor: disabledTextColor ??
                Colors.white, // Set the disabled text color
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
              side: BorderSide(
                color: borderColor ??
                    Colors
                        .transparent, // Use borderColor or default to transparent
                width: borderWidth ??
                    0, // Use borderWidth or default to 0 (no border)
              ),
            ),
          ),
          onPressed: onPressed,
          child: child,
        ),
      ),
    );
  }
}
