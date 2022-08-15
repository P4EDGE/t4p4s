%{!?t4p4sroot: %global t4p4sroot /root/t4p4s}
%{!?shortname: %global shortname t4p4s}

Name:           p4edge-t4p4s
Version:        0.0.0
Release:        0%{?dist}
Summary:        P4Edge t4p4s
License:        Apache 2.0
URL:            https://github.com/p4edge/t4p4s
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
Requires:       python3, python3-pip, ccache
BuildRequires:  debbuild-macros-systemd
Packager:       Dávid Kis <kidraai@.inf.elte.hu>

%description
P4Edge t4p4s

%prep
%autosetup
cp ./packaging/find_system_p4test.patch ./src/hlir16/
cd ./src/hlir16/
git apply find_system_p4test.patch

%build

%install

rm -rf %{buildroot}

mkdir -p %{buildroot}%{t4p4sroot}
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_unitdir}

install -m 755 packaging/setup_eth_wlan_bridge.sh %{buildroot}%{t4p4sroot}
install -m 755 packaging/%{shortname}-start %{buildroot}%{_bindir}
install -m 755 packaging/%{shortname}-p4rtshell %{buildroot}%{_bindir}
install -m 644 packaging/%{shortname}.service %{buildroot}%{_unitdir}
cp -r ./* %{buildroot}%{t4p4sroot}

%post
python3 -m pip install -r %{t4p4sroot}/requirements.txt
%systemd_post %{shortname}.service

%preun
%systemd_preun %{shortname}.service

%postun
%systemd_postun %{shortname}.service

%files
%{_bindir}/*
%{_unitdir}/%{shortname}.service
%{t4p4sroot}/examples/*
%{t4p4sroot}/src/*
%{t4p4sroot}/*
