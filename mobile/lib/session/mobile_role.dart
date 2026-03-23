enum MobileRole {
  employee(code: 'employee'),
  fieldSupervisor(code: 'field_supervisor'),
  restrictedField(code: 'restricted_field');

  const MobileRole({required this.code});

  final String code;

  static MobileRole fromRoleKeys(Iterable<String> roleKeys) {
    if (roleKeys.contains('field_supervisor')) {
      return MobileRole.fieldSupervisor;
    }
    if (roleKeys.contains('restricted_field')) {
      return MobileRole.restrictedField;
    }
    return MobileRole.employee;
  }
}
