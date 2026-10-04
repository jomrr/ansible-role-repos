# Ansible Role: repos

![GitHub](https://img.shields.io/github/license/jomrr/ansible-role-repos)
![GitHub last commit](https://img.shields.io/github/last-commit/jomrr/ansible-role-repos)
![GitHub issues](https://img.shields.io/github/issues-raw/jomrr/ansible-role-repos)
[![dev](https://img.shields.io/github/actions/workflow/status/jomrr/ansible-role-repos/dev.yml?branch=dev&label=dev)](https://github.com/jomrr/ansible-role-repos/actions/workflows/dev.yml?query=branch%3Adev)
[![main](https://img.shields.io/github/actions/workflow/status/jomrr/ansible-role-repos/main.yml?branch=main&label=main)](https://github.com/jomrr/ansible-role-repos/actions/workflows/main.yml?query=branch%3Amain)

Ansible role for managing explicitly selected package repositories with APT, DNF
and Zypper.

## Purpose

Manage explicitly selected package repositories on AlmaLinux,
Debian, Fedora, openSUSE Leap, openSUSE Tumbleweed and Ubuntu. Empty
inputs make no changes. Repeated application of unchanged inputs is
idempotent.

Declare repositories in `repos_apt`, `repos_dnf` or `repos_zypper`.
Only the list matching the detected package manager is applied; DNF
and DNF5 share a backend. Every entry describes desired state,
whether the repository is new, supplied by the distribution or
selected through a preset. There is no operation mode.

`state: present` creates a missing repository or converges the
supplied settings; `enabled: false` disables it without removing it,
and `state: absent` removes it. Unspecified fields of supplied
repositories are preserved. New repositories use `repos_enabled` and
`repos_gpgcheck` as applicable. Entries override these policies.
`repos_state` supplies the default presence. Omitting an entry
leaves its last configuration intact.

RPM entries identify a section with `name` and optionally `file`, a
filename stem below the backend repository directory. `file`
defaults to `name`. DNF URLs use `baseurl`, `metalink` or
`mirrorlist`; Zypper uses `repo`. Choosing a URL removes alternative
mirror sources. Changes preserve unrelated options, sections and
comments. Creation requires a URL. Removing the last section removes
its file.

APT entries identify a `.sources` file with `name`, or an absolute
`.sources` or legacy `.list` `path`. `suites` selects all matching
sources, including disabled and `deb-src` entries; omitting it
selects the whole file. New DEB822 sources require `suites` and
`uris`, plus `components` unless suites are exact paths ending in
`/`. Supplied stanzas retain unspecified fields and are split when
selected suites need different settings. Missing suites are created
only with the required fields. `state: absent` with suites removes
those suites; without suites it removes the selected file. Legacy
`.list` files support `uris`, `enabled` and `state` for supplied
suites, with exactly one URI. Use DEB822 for new sources.

Select a distribution preset with `preset: epel` or `preset:
backports` in the same backend list. Additional fields on that entry
override the preset defaults. Selected presets default to
`repos_enabled`; `enabled: false` disables them. For a preset
containing several repositories, named entries under `repositories`
provide individual overrides. RPM URL overrides replace inherited
alternatives. Presets supply target identities; `name`, `file` and
`path` cannot accompany `preset`.

Presets provide repository definitions with distribution-specific
URLs, signing keys or related repositories. RPM repositories supplied
by the distribution are selected directly with `name` and `file`.

The role rejects repeated RPM IDs, including IDs expanded from
presets. APT entries in the same file must select disjoint suites.
Source paths must be normalized; APT symlinks are rejected. APT
validates changed files before replacement without downloading
metadata.

## Scope

### Managed

- Desired presence, enabled state and settings of explicitly selected
  repositories.
- Distribution presets and private mirrors declared within each backend list.

### Not Managed

- Repositories omitted from the input, package installation or distribution
  upgrades.
- Repository credentials; use separate package-manager credential configuration.
- APT and DNF metadata refresh, or removal of signing keys.

## Requirements

- jomrr.general >=1.1.0 provides the repository modules and preset resolver.
- community.general provides Ansible's Zypper package backend.

## Dependencies

```yaml
collections:
  - name: jomrr.general
    version: '>=1.1.0'
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

Enabled flag for new repositories and selected presets; omitted settings of
supplied repositories remain unchanged.

Default:

```yaml
repos_enabled: true
```

### `repos_gpgcheck`

Type: `bool`. Required: `false`.

Signature verification for new RPM repositories; item settings override this
policy.

Default:

```yaml
repos_gpgcheck: true
```

### `repos_apt`

Type: `list`. Required: `false`.

Desired APT repositories, selected presets and supplied sources; unspecified
settings are preserved.

Default:

```yaml
repos_apt: []
```

### `repos_dnf`

Type: `list`. Required: `false`.

Desired DNF repositories, selected presets and supplied sources; unspecified
settings are preserved.

Default:

```yaml
repos_dnf: []
```

### `repos_zypper`

Type: `list`. Required: `false`.

Desired ZYPPER repositories, selected presets and supplied sources; unspecified
settings are preserved.

Default:

```yaml
repos_zypper: []
```

## Managed Files

- `APT: /etc/apt/sources.list.d/<name>.sources or an explicit path.`
- `DNF: /etc/yum.repos.d/<file-or-name>.repo.`
- `Zypper: /etc/zypp/repos.d/<file-or-name>.repo.`
- `Binary APT signing keys downloaded from HTTPS are stored under
  /etc/apt/keyrings/<URL-hash>.gpg.`

## Check Mode

Repository changes support check mode on every backend.

- APT file diffs are omitted because supplied files can contain credentials.
- Zypper signing-key import and metadata refresh are skipped in check mode.

## Service Behavior

No service is managed. Changed Zypper repositories refresh when auto_import_keys
is enabled.

## Security Notes

- RPM signature checking defaults to true for new repositories; DNF TLS
  verification defaults to enabled.
- Use signed_by to scope APT signing keys. HTTPS armored keys are embedded;
  binary keys use a scoped keyring.
- OBS presets import the selected repository signing key when its settings
  change.

## Operational Notes

- Previously downloaded `/etc/apt/keyrings/repos-<URL-hash>.gpg` files are
  retained; they are not removed automatically.
- AlmaLinux presets: epel. Fedora: rpmfusion_free and rpmfusion_nonfree.
  openSUSE: obs_devel_tools and obs_filesystems. Debian and Ubuntu: backports.
- APT names use lowercase letters, digits and hyphens. RPM file stems allow
  letters, digits, dots, underscores and hyphens, without the .repo suffix.
- Backports uses the detected release codename and installed archive keyring.
  Debian enables main; Ubuntu enables main, restricted, universe and multiverse
  and uses the ports archive on non-x86 architectures.
- The backports preset targets debian-backports.sources or
  ubuntu-backports.sources. For Backports already present in ubuntu.sources or
  another file, declare that path and its suite directly to avoid a duplicate
  source.
- No unselected preset is managed. CRB uses `name: crb` and `file:
  almalinux-crb`; Fedora testing uses `name: updates-testing` and `file:
  fedora-updates-testing`.
- Enable CRB explicitly alongside epel for packages depending on CRB, and select
  rpmfusion_free alongside rpmfusion_nonfree for Nonfree packages depending on
  Free.
- OBS presets select devel:tools and filesystems for the detected release. Other
  projects can be declared directly in repos_zypper.
- APT and DNF metadata is refreshed by consuming package tasks. Zypper
  auto_import_keys refreshes the selected repository after changes; autorefresh
  controls later refreshes.

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

### Declare a repository and a preset

Create the organization source and enable release-matched Backports.

```yaml
- name: Configure APT repositories
  hosts: debian:ubuntu
  gather_facts: true
  roles:
    - role: jomrr.repos
      repos_apt:
        - name: organization
          uris: [https://packages.example.org/debian]
          suites: [stable]
          components: [main]
          signed_by: /etc/apt/keyrings/organization.asc
        - preset: backports
```

### Declare Fedora repository settings

Use a private release mirror, disable testing and enable RPM Fusion.

```yaml
- name: Configure Fedora repositories
  hosts: fedora
  gather_facts: true
  roles:
    - role: jomrr.repos
      repos_dnf:
        - name: fedora
          file: fedora
          enabled: true
          baseurl: [https://mirror.example.org/fedora/releases/$releasever/Everything/$basearch/os]
        - name: updates-testing
          file: fedora-updates-testing
          enabled: false
        - preset: rpmfusion_free
```

### Declare AlmaLinux repository mirrors

Use private mirrors for EPEL and the supplied CRB repository.

```yaml
- name: Configure Enterprise Linux mirrors
  hosts: almalinux
  gather_facts: true
  roles:
    - role: jomrr.repos
      repos_dnf:
        - preset: epel
          baseurl: [https://mirror.example.org/epel/$releasever/Everything/$basearch]
        - name: crb
          file: almalinux-crb
          enabled: true
          baseurl: [https://mirror.example.org/almalinux/$releasever/CRB/$basearch/os]
```

### Select a section whose ID differs from its filename

Manage [extras] in almalinux-extras.repo while preserving its other supplied settings.

```yaml
- name: Configure AlmaLinux Extras
  hosts: almalinux
  gather_facts: true
  roles:
    - role: jomrr.repos
      repos_dnf:
        - name: extras
          file: almalinux-extras
          enabled: true
```

### Manage package-supplied RPM Fusion repositories

For hosts with rpmfusion-free-release installed, declare desired
overrides of its supplied repository sections.

```yaml
- name: Configure package-supplied RPM Fusion mirrors
  hosts: fedora
  gather_facts: true
  roles:
    - role: jomrr.repos
      repos_dnf:
        - name: rpmfusion-free
          file: rpmfusion-free
          enabled: true
          baseurl: [https://mirror.example.org/rpmfusion/free/fedora/releases/$releasever/Everything/$basearch/os]
        - name: rpmfusion-free-updates
          file: rpmfusion-free-updates
          enabled: true
          baseurl: [https://mirror.example.org/rpmfusion/free/fedora/updates/$releasever/$basearch]
```

### Declare RPM Fusion mirrors

Override release and updates URLs within one selected preset.

```yaml
- name: Configure RPM Fusion
  hosts: fedora
  gather_facts: true
  roles:
    - role: jomrr.repos
      repos_dnf:
        - preset: rpmfusion_free
          repositories:
            - name: rpmfusion-free
              baseurl: [https://mirror.example.org/rpmfusion/free/fedora/releases/$releasever/Everything/$basearch/os]
            - name: rpmfusion-free-updates
              baseurl: [https://mirror.example.org/rpmfusion/free/fedora/updates/$releasever/$basearch]
```

### Declare the mirror for supplied Ubuntu Backports

Preserve the other suites, fields and comments in ubuntu.sources.

```yaml
- name: Configure the Ubuntu Backports mirror
  hosts: ubuntu
  gather_facts: true
  roles:
    - role: jomrr.repos
      repos_apt:
        - path: /etc/apt/sources.list.d/ubuntu.sources
          suites: ["{{ ansible_facts.distribution_release }}-backports"]
          uris: [https://mirror.example.org/ubuntu]
```

### Declare openSUSE repositories

Enable an OBS preset and disable a supplied repository by its alias.

```yaml
- name: Configure openSUSE repositories
  hosts: opensuse
  gather_facts: true
  roles:
    - role: jomrr.repos
      repos_zypper:
        - preset: obs_devel_tools
        - name: repo-oss
          enabled: false
```

## References

- [Repository modules and filter](https://github.com/jomrr/ansible-collection-general)
- [Debian Backports](https://backports.debian.org/Instructions/)
- [Ubuntu archive pockets](https://documentation.ubuntu.com/project/how-ubuntu-is-made/concepts/package-archive/)
- [AlmaLinux repositories](https://wiki.almalinux.org/repos/Extras)
- [RPM Fusion definitions](https://github.com/rpmfusion/rpmfusion-free-release)
- [OBS devel:tools](https://build.opensuse.org/repositories/devel%3Atools)

## Author

[Jonas Mauer](https://github.com/jomrr)

## License

This project is licensed under the MIT License.
See [LICENSE](LICENSE) for the full license text.

Copyright (c) 2026 Jonas Mauer.
