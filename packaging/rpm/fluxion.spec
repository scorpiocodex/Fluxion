Name:           fluxion
Version:        0.1.0
Release:        1%{?dist}
Summary:        The Intelligent Network Command Engine

License:        MIT
URL:            https://github.com/fluxion-net/fluxion
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
Requires:       python3 >= 3.11

%description
Fluxion is a next-generation CLI network transport engine
with HTTP/2, HTTP/3 QUIC, parallel downloads, adaptive
concurrency, and a Sci-Fi Quantum Command HUD interface.

%prep
%autosetup

%install
pip3 install --root=%{buildroot} --no-deps .

%files
%{python3_sitelib}/fluxion/
%{_bindir}/fluxion

%changelog
* Mon Jan 01 2026 Fluxion Contributors <fluxion@example.com> - 0.1.0-1
- Initial release
