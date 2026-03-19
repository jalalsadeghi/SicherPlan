import 'package:flutter/material.dart';

enum AppDestination {
  home(id: 'home', icon: Icons.dashboard_rounded),
  schedule(id: 'schedule', icon: Icons.calendar_month_rounded),
  updates(id: 'updates', icon: Icons.campaign_rounded),
  timeCapture(id: 'timeCapture', icon: Icons.timer_outlined),
  patrol(id: 'patrol', icon: Icons.shield_outlined),
  profile(id: 'profile', icon: Icons.person_outline_rounded);

  const AppDestination({required this.id, required this.icon});

  final String id;
  final IconData icon;
}
