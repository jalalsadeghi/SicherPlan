import 'package:flutter/material.dart';

import '../../api/mobile_backend.dart';
import '../../l10n/app_localizations.dart';
import '../../session/mobile_session_controller.dart';
import '../../widgets/highlight_card.dart';
import '../../widgets/shell_scaffold.dart';

class WatchbookScreen extends StatefulWidget {
  const WatchbookScreen({
    required this.controller,
    required this.backend,
    super.key,
  });

  final MobileSessionController controller;
  final MobileBackendGateway backend;

  @override
  State<WatchbookScreen> createState() => _WatchbookScreenState();
}

class _WatchbookScreenState extends State<WatchbookScreen> {
  late Future<(List<WatchbookListItem>, List<EmployeeReleasedScheduleItem>)> _future;
  WatchbookReadModel? _selected;
  final TextEditingController _entryController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  @override
  void dispose() {
    _entryController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return ShellScaffold(
      title: l10n.watchbookTitle,
      subtitle: l10n.watchbookSubtitle,
      children: [
        FutureBuilder<(List<WatchbookListItem>, List<EmployeeReleasedScheduleItem>)>(
          future: _future,
          builder: (context, snapshot) {
            if (snapshot.connectionState != ConnectionState.done) {
              return const Padding(
                padding: EdgeInsets.symmetric(vertical: 32),
                child: Center(child: CircularProgressIndicator()),
              );
            }
            if (snapshot.hasError) {
              return HighlightCard(
                title: l10n.watchbookTitle,
                subtitle: l10n.mobileLoadErrorSubtitle(snapshot.error),
                icon: Icons.error_outline_rounded,
              );
            }
            final data = snapshot.data ?? (const <WatchbookListItem>[], const <EmployeeReleasedScheduleItem>[]);
            final watchbooks = data.$1;
            final schedules = data.$2;
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (schedules.isNotEmpty) ...[
                  Text(l10n.scheduleTitle, style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: schedules
                        .where((item) => item.planningRecordId != null || item.orderId != null || item.siteId != null)
                        .map(
                          (item) => ActionChip(
                            label: Text('${item.shiftLabel} · ${item.scheduleDate.toLocal().toString().split(' ').first}'),
                            onPressed: () => _openFromSchedule(item),
                          ),
                        )
                        .toList(),
                  ),
                  const SizedBox(height: 16),
                ],
                if (watchbooks.isEmpty)
                  HighlightCard(
                    title: l10n.watchbookTitle,
                    subtitle: l10n.watchbookPlaceholderSubtitle,
                    icon: Icons.menu_book_outlined,
                  )
                else
                  ...watchbooks.map(
                    (item) => Card(
                      child: ListTile(
                        title: Text(item.headline ?? item.contextType),
                        subtitle: Text('${item.logDate.toLocal().toString().split(' ').first} · ${item.closureStateCode}'),
                        onTap: () => _loadWatchbook(item.id),
                      ),
                    ),
                  ),
                if (_selected != null) ...[
                  const SizedBox(height: 16),
                  Text(_selected!.headline ?? _selected!.contextType, style: Theme.of(context).textTheme.titleLarge),
                  const SizedBox(height: 8),
                  ..._selected!.entries
                      .map(
                        (entry) => Card(
                          child: ListTile(
                            title: Text(entry.narrative),
                            subtitle: Text('${entry.entryTypeCode} · ${entry.authorActorType}'),
                          ),
                        ),
                      )
                      ,
                  const SizedBox(height: 12),
                  TextField(
                    controller: _entryController,
                    minLines: 3,
                    maxLines: 5,
                    decoration: InputDecoration(
                      labelText: l10n.watchbookEntryLabel,
                      border: const OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 8),
                  FilledButton(
                    onPressed: _selected!.closureStateCode == 'open' ? _submitEntry : null,
                    child: Text(l10n.watchbookEntryAction),
                  ),
                ],
              ],
            );
          },
        ),
      ],
    );
  }

  Future<(List<WatchbookListItem>, List<EmployeeReleasedScheduleItem>)> _load() async {
    final tenantId = widget.controller.context?.tenantId ?? '';
    return widget.controller.withAccessToken((token) async {
      final watchbooks = await widget.backend.fetchWatchbooks(token, tenantId);
      final schedules = await widget.backend.fetchReleasedSchedules(token);
      return (watchbooks, schedules);
    });
  }

  Future<void> _loadWatchbook(String watchbookId) async {
    final tenantId = widget.controller.context?.tenantId ?? '';
    final item = await widget.controller.withAccessToken(
      (token) => widget.backend.fetchWatchbook(token, tenantId: tenantId, watchbookId: watchbookId),
    );
    if (!mounted) return;
    setState(() {
      _selected = item;
    });
  }

  Future<void> _openFromSchedule(EmployeeReleasedScheduleItem item) async {
    final tenantId = widget.controller.context?.tenantId ?? '';
    final watchbook = await widget.controller.withAccessToken(
      (token) => widget.backend.openWatchbook(
        token,
        tenantId: tenantId,
        contextType: item.planningRecordId != null
            ? 'planning_record'
            : item.orderId != null
                ? 'order'
                : 'site',
        logDate: item.scheduleDate,
        planningRecordId: item.planningRecordId,
        orderId: item.orderId,
        siteId: item.siteId,
        shiftId: item.shiftId,
        headline: item.shiftLabel,
      ),
    );
    if (!mounted) return;
    setState(() {
      _selected = watchbook;
      _future = _load();
    });
  }

  Future<void> _submitEntry() async {
    final selected = _selected;
    if (selected == null || _entryController.text.trim().isEmpty) return;
    final tenantId = widget.controller.context?.tenantId ?? '';
    await widget.controller.withAccessToken(
      (token) => widget.backend.createWatchbookEntry(
        token,
        tenantId: tenantId,
        watchbookId: selected.id,
        entryTypeCode: 'employee_note',
        narrative: _entryController.text.trim(),
      ),
    );
    _entryController.clear();
    await _loadWatchbook(selected.id);
    if (!mounted) return;
    setState(() {
      _future = _load();
    });
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(context.l10n.watchbookEntrySaved)),
    );
  }
}
