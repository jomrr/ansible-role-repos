# Ansible Role: repos

![GitHub](https://img.shields.io/github/license/jomrr/ansible-role-repos)
![GitHub last commit](https://img.shields.io/github/last-commit/jomrr/ansible-role-repos)
![GitHub issues](https://img.shields.io/github/issues-raw/jomrr/ansible-role-repos)
[![dev](https://img.shields.io/github/actions/workflow/status/jomrr/ansible-role-repos/dev.yml?branch=dev&label=dev)](https://github.com/jomrr/ansible-role-repos/actions/workflows/dev.yml?query=branch%3Adev)
[![main](https://img.shields.io/github/actions/workflow/status/jomrr/ansible-role-repos/main.yml?branch=main&label=main)](https://github.com/jomrr/ansible-role-repos/actions/workflows/main.yml?query=branch%3Amain)

Ansible role for managing explicitly selected package repositories with APT, DNF
and Zypper.

## Purpose

Manage explicitly selected package repositories on AlmaLinux, Debian,
Fedora, openSUSE Leap, openSUSE Tumbleweed and Ubuntu. Empty inputs make
no changes. Repeated application of unchanged inputs is idempotent.

`repos_apt`, `repos_dnf` and `repos_zypper` describe complete repository
definitions. Only the list matching the detected package manager is applied;
DNF and DNF5 share the DNF backend. `repos_toggles` changes only `enabled`
in a supplied RPM repository section, preserving other options and comments.

Every definition requires `name`. `state` and `enabled` override `repos_state`
and `repos_enabled` per item. APT entries with `state: present` also require
`uris` and `suites`; non-path suites require `components`. Optional APT fields
are `types`, `architectures` and `signed_by`.

DNF entries with `state: present` require `baseurl`, `metalink` or `mirrorlist`.
Optional fields are `file`, `description`, `gpgkey`, `gpgcheck`,
`repo_gpgcheck`,
`priority`, `exclude` and `includepkgs`. `baseurl`, `gpgkey`, `exclude` and
`includepkgs` are lists of strings. Zypper entries with `state: present`
require `repo`; optional fields are `description`, `gpgcheck`, `autorefresh`,
`auto_import_keys` and `priority`. `gpgcheck` overrides `repos_gpgcheck`.

Toggle entries require `path`, `section` and `enabled`. They always preserve
the rest of the selected file; the complete-definition policies do not apply.

## Scope

### Managed

- Creation, modification, disabling and removal of explicitly defined
  repositories.
- Enabled flags in explicitly selected RPM repository files and sections.
- Distribution presets selected by name under repos_presets.

### Not Managed

- Repositories omitted from the input, package installation or distribution
  upgrades.
- Repository credentials; use the package manager's separate credential
  configuration.
- Cache refresh for APT and DNF, or removal of externally provisioned signing
  keys.

## Requirements

- community.general provides ini_file and zypper_repository.
- APT uses python3-debian; the role enables the module's automatic installation
  with the system Python.

## Dependencies

```yaml
collections:
  - name: community.general
    version: '>=12.0.0'
  - name: ansible.posix
    version: '>=2.0.0'
```

## Role Variables

### `repos_state`

Type: `str`. Required: `false`.

Desired state of explicitly defined repositories.

Default:

```yaml
repos_state: present
```

### `repos_enabled`

Type: `bool`. Required: `false`.

Default enabled flag for explicitly defined repositories.

Default:

```yaml
repos_enabled: true
```

### `repos_gpgcheck`

Type: `bool`. Required: `false`.

Default signature verification for RPM packages.

Default:

```yaml
repos_gpgcheck: true
```

### `repos_apt`

Type: `list`. Required: `false`.

Complete DEB822 definitions for APT; unlisted sources are preserved.

Default:

```yaml
repos_apt: []
```

### `repos_dnf`

Type: `list`. Required: `false`.

Complete DNF or DNF5 definitions; listed sections are fully owned by this role.

Default:

```yaml
repos_dnf: []
```

### `repos_zypper`

Type: `list`. Required: `false`.

Complete Zypper definitions; listed repositories are fully owned by this role.

Default:

```yaml
repos_zypper: []
```

### `repos_toggles`

Type: `list`. Required: `false`.

Change only enabled in supplied RPM repository sections.

Default:

```yaml
repos_toggles: []
```

### `repos_presets`

Type: `dict`. Required: `false`.

Named distribution switches; omitted means unmanaged, true enables and false
disables.

Default:

```yaml
repos_presets: {}
```

## Managed Files

- `APT: /etc/apt/sources.list.d/<name>.sources and module-managed keys in
  /etc/apt/keyrings.`
- `DNF: /etc/yum.repos.d/<file-or-name>.repo.`
- `Zypper: /etc/zypp/repos.d/<name>.repo.`
- `Explicit paths supplied through repos_toggles.`

## Check Mode

APT and DNF definitions and RPM enabled flags support check mode.

- python3-debian must already be installed for the first APT check-mode run.
- community.general.zypper_repository does not support check mode; Zypper
  definitions are skipped by that module.

## Service Behavior

No service or handler is managed.

## Security Notes

- RPM signature checking defaults to true; DNF TLS verification remains enabled.
- Use signed_by to scope APT signing keys to a repository instead of adding
  global trust.
- OBS presets import the selected repository's signing key when adding or
  changing it.

## Operational Notes

- Complete definitions own their listed sections. Use repos_toggles for supplied
  repositories such as fedora in fedora.repo; it requires the file and section
  to exist.
- Definition names are lowercase filename stems containing letters, digits and
  hyphens. DNF file overrides also allow dots and underscores, without the .repo
  suffix.
- Removal requires state: absent and name; for a DNF file override, also supply
  file. Unlisted repositories remain unchanged, including when inputs return to
  empty lists.
- repos_presets accepts epel and crb on AlmaLinux; rpmfusion_free,
  rpmfusion_nonfree and updates_testing on Fedora; obs_devel_tools and
  obs_filesystems on openSUSE. Debian and Ubuntu have no predefined switches.
- Omitted presets are unmanaged. Explicit true or false creates a complete
  preset definition with that enabled flag, except crb and updates_testing,
  which only toggle supplied sections. EPEL and RPM Fusion presets own their
  named sections; use repos_toggles to preserve a previously customized
  definition instead.
- Select crb alongside epel for EPEL packages that depend on CRB, and select
  rpmfusion_free alongside rpmfusion_nonfree for Nonfree packages that depend on
  Free.
- OBS presets point to devel:tools and filesystems builds for the detected
  openSUSE release. Other OBS projects can be supplied through repos_zypper.
- Presets and custom definitions cannot manage the same repository twice. A
  section cannot appear in both complete definitions and repos_toggles in one
  invocation.
- APT and DNF metadata is refreshed by the consuming package task. Zypper
  auto_import_keys refreshes only the repository being added or changed;
  autorefresh controls later refreshes.

## Supported Platforms

| OS Family | Distribution | Version | Container Image |
| --------- | ------------ | ------- | --------------- |
| RedHat | AlmaLinux | latest | [jomrr/molecule-almalinux:latest](https://hub.docker.com/r/jomrr/molecule-almalinux) |
| Debian | Debian | latest | [jomrr/molecule-debian:latest](https://hub.docker.com/r/jomrr/molecule-debian) |
| RedHat | Fedora | latest | [jomrr/molecule-fedora:latest](https://hub.docker.com/r/jomrr/molecule-fedora) |
| Suse | OpenSuse Leap | latest | [jomrr/molecule-opensuse-leap:latest](https://hub.docker.com/r/jomrr/molecule-opensuse-leap) |
| Suse | OpenSuse Tumbleweed | latest | [jomrr/molecule-opensuse-tumbleweed:latest](https://hub.docker.com/r/jomrr/molecule-opensuse-tumbleweed) |
| Debian | Ubuntu | latest | [jomrr/molecule-ubuntu:latest](https://hub.docker.com/r/jomrr/molecule-ubuntu) |

## Example Playbook

### Define an APT repository

Use an existing public keyring scoped to one DEB822 source.

```yaml
- name: Configure APT repositories
  hosts: debian
  gather_facts: true
  roles:
    - role: jomrr.repos
      repos_apt:
        - name: organization
          uris: [https://packages.example.org/debian]
          suites: [stable]
          components: [main]
          signed_by: /etc/apt/keyrings/organization.asc
```

### Toggle supplied Fedora repositories

Preserve the supplied definitions, including their URLs, keys and comments.

```yaml
- name: Configure Fedora repositories
  hosts: fedora
  gather_facts: true
  roles:
    - role: jomrr.repos
      repos_toggles:
        - path: /etc/yum.repos.d/fedora.repo
          section: fedora
          enabled: true
      repos_presets:
        updates_testing: false
        rpmfusion_free: true
```

### Select AlmaLinux presets

Define EPEL and enable the supplied CRB repository.

```yaml
- name: Configure Enterprise Linux repositories
  hosts: almalinux
  gather_facts: true
  roles:
    - role: jomrr.repos
      repos_presets:
        epel: true
        crb: true
```

### Select an OBS repository

Enable devel:tools for the detected openSUSE release.

```yaml
- name: Configure openSUSE repositories
  hosts: opensuse
  gather_facts: true
  roles:
    - role: jomrr.repos
      repos_presets:
        obs_devel_tools: true
```

## References

- [DEB822 module](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/deb822_repository_module.html)
- [AlmaLinux repositories](https://wiki.almalinux.org/repos/Extras)
- [RPM Fusion definitions](https://github.com/rpmfusion/rpmfusion-free-release)
- [OBS devel:tools](https://build.opensuse.org/repositories/devel%3Atools)

## Author

[Jonas Mauer](https://github.com/jomrr)

## License

This project is licensed under the MIT License.
See [LICENSE](LICENSE) for the full license text.

Copyright (c) 2026 Jonas Mauer.
