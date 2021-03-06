# We have to override the new %%install behavior because, well... the kernel is special.
%global __spec_install_pre %{___build_pre}

# What parts do we want to build?  We must build at least one kernel.
# These are the kernels that are built IF the architecture allows it.
# All should default to 1 (enabled) and be flipped to 0 (disabled)
# by later arch-specific checks.

# The following build options are enabled by default.
# Use either --without <opt> in your rpmbuild command or force values
# to 0 in here to disable them.
#

# kernel-headers
%define with_headers   %{?_without_headers:   0} %{?!_without_headers:   1}
# perf
%define with_perf      %{?_without_perf:      0} %{?!_without_perf:      1}
# tools
%define with_tools     %{?_without_tools:     0} %{?!_without_tools:     1}
# kernel-debuginfo
%define with_debuginfo %{?_without_debuginfo: 1} %{?!_without_debuginfo: 0}


#
# Additional options for user-friendly one-off kernel building:
#
# Only build the base kernel (--with baseonly):
%define with_baseonly   %{?_with_baseonly:      1} %{?!_with_baseonly:     0}
#
# Cross compile requested?
%define with_cross      %{?_with_cross:         1} %{?!_with_cross:        0}
#
# build a release kernel on rawhide
%define with_release    %{?_with_release:       1} %{?!_with_release:      0}

# Want to build a vanilla kernel build without any non-upstream patches?
%define with_vanilla    %{?_with_vanilla:       1} %{?!_with_vanilla: 0}

# Build the RPi bcm270x linux kernel port
%define with_bcm270x    %{?_without_bcm270x:    0} %{?!_without_bcm270x: 1}

# By default build without rt-preempt version
%define with_rt_preempt %{?_with_rt_preempt:    1} %{?!_with_rt_preempt: 0}

# Enable Large Physical Address Extension support
%define with_lpae       %{?_with_lpae:       1} %{?!_with_lpae: 0}

# For a stable, released kernel, released_kernel should be 1. For rawhide
# and/or a kernel built from an rc or git snapshot, released_kernel should
# be 0.
%global released_kernel 1

# baserelease defines which build revision of this kernel version we're
# building.  We used to call this fedora_build, but the magical name
# baserelease is matched by the rpmdev-bumpspec tool, which you should use.
#
# We used to have some extra magic weirdness to bump this automatically,
# but now we don't.  Just use: rpmdev-bumpspec -c 'comment for changelog'
# When changing base_sublevel below or going from rc to a final kernel,
# reset this by hand to 1 (or to 0 and then use rpmdev-bumpspec).
# scripts/rebase.sh should be made to do that for you, actually.
#
# NOTE: baserelease must be > 0 or bad things will happen if you switch
#       to a released kernel (released version will be < rc version)
#
# For non-released -rc kernels, this will be appended after the rcX and
# gitX tags, so a 3 here would become part of release "0.rcX.gitX.3"
#
%global baserelease 1

# RaspberryPi foundation git snapshot (short)
%global rpi_gitshort 52cf298f

%global fedora_build %{baserelease}

# Enable rt preempt build support
# Only enable if there are available patches
%global enable_preempt 0

%if %{enable_preempt}
# Real-Time kernel defines
%global rtrelease 20
%global rt_stable_update 30

%if %{with_rt_preempt}
%global fedora_build %{baserelease}.rt%{rtrelease}
%endif
%endif

%if %{with_lpae}
%global fedora_build %{baserelease}.lpae
%endif

# base_sublevel is the kernel version we're starting with and patching
# on top of -- for example, 3.1-rc7-git1 starts with a 3.0 base,
# which yields a base_sublevel of 0.
%define base_sublevel 13

## If this is a released kernel ##
%if 0%{?released_kernel}

# Do we have a -stable update to apply?
%define stable_update 5

# Set rpm version accordingly
%if 0%{?stable_update}
%define stablerev %{stable_update}
%define stable_base %{stable_update}
%endif
%define rpmversion 4.%{base_sublevel}.%{stable_update}

## The not-released-kernel case ##
%else
# The next upstream release sublevel (base_sublevel+1)
%define upstream_sublevel %(echo $((%{base_sublevel} + 1)))
# The rc snapshot level
%define rcrev 0
# The git snapshot level
%define gitrev 0
# Set rpm version accordingly
%define rpmversion 4.%{upstream_sublevel}.0
%endif
# Nb: The above rcrev and gitrev values automagically define Source1 and Source2 below.

%if 0%{!?nopatches:1}
%define nopatches 0
%endif

%if %{with_vanilla}
%define nopatches 1
%endif

%if %{nopatches}
%define variant -vanilla
%endif

%if %{with_bcm270x}
 %define bcm270x 1
 %define Flavour rpi
 %define buildid .%{Flavour}
%else
 %define bcm270x 0
%endif


# pkg_release is what we'll fill in for the rpm Release: field
%define pkg_release %{fedora_build}%{?buildid}%{?dist}


# The kernel tarball/base version
%define kversion 4.%{base_sublevel}

%define make_target bzImage
%define kernel_image arch/arm/boot/zImage
%define KVERREL %{version}-%{release}.%{_target_cpu}
%define asmarch arm
%define hdrarch arm
%define image_install_path boot
# http://lists.infradead.org/pipermail/linux-arm-kernel/2012-March/091404.html
%define kernel_mflags KALLSYMS_EXTRA_PASS=1


# Overrides for generic default options

# don't build noarch kernels or headers (duh)
%ifarch noarch
%define with_headers 0
%define with_tools 0
%define with_perf 0
%endif


# Should make listnewconfig fail if there's config options
# printed out?
%if %{nopatches}
%define listnewconfig_fail 0
%else
%define listnewconfig_fail 1
%endif

#
# Packages that need to be installed before the kernel is, because the %%post
# scripts use them.
#
%define kernel_prereq  fileutils, systemd, grubby
%define initrd_prereq  dracut


Name: kernel%{?variant}
Group: System Environment/Kernel
License: GPLv2 and Redistributable, no modification permitted
%if !%{bcm270x}
Summary: The Linux kernel for the Raspberry Pi (BCM283x)
URL: http://www.kernel.org
%else
%if %{_target_cpu} == armv7hl
Summary: The BCM2709 Linux kernel port for the Raspberry Pi 2 and 3 Model B
%else
Summary: The BCM2708 Linux kernel port for the Raspberry Pi Model A, B and Zero
%endif
URL: https://github.com/raspberrypi/linux
%endif
Version: %{rpmversion}
Release: %{pkg_release}
ExclusiveArch: %{arm}
ExclusiveOS: Linux
Requires: kernel-core-uname-r = %{KVERREL}%{?variant}
Requires: kernel-modules-uname-r = %{KVERREL}%{?variant}


#
# List the packages used during the kernel build
#
BuildRequires: kmod, patch, bash, sh-utils, tar
BuildRequires: bzip2, xz, findutils, gzip, m4, perl, perl-Carp, make, diffutils, gawk
BuildRequires: gcc, binutils, redhat-rpm-config, hmaccalc
BuildRequires: net-tools, hostname, bc
%if %{with_rt_preempt}
BuildRequires: quilt
%endif

%if %{with_perf}
BuildRequires: elfutils-devel zlib-devel binutils-devel newt-devel python-devel perl(ExtUtils::Embed) bison flex
BuildRequires: audit-libs-devel
%endif
%if %{with_tools}
BuildRequires: pciutils-devel gettext ncurses-devel asciidoc
%endif
BuildConflicts: rhbuildsys(DiskFree) < 500Mb
%if %{with_debuginfo}
BuildRequires: rpm-build, elfutils
%define debuginfo_args --strict-build-id -r
%endif

%if %{with_cross}
BuildRequires: binutils-%{_build_arch}-linux-gnu, gcc-%{_build_arch}-linux-gnu
%define cross_opts CROSS_COMPILE=%{_build_arch}-linux-gnu-
%endif

Source0: https://www.kernel.org/pub/linux/kernel/v4.x/linux-%{kversion}.tar.xz
Source10: perf-man-%{kversion}.tar.gz
Source16: mod-extra.list
Source17: mod-extra.sh
Source99: filter-modules.sh

# kernel config modifications 
Source1000: bcm270x.cfg
Source1100: bcm283x.cfg

%if %{enable_preempt}
# rt kernel config modification
%if 0%{?rt_stable_update}
Source1500: https://www.kernel.org/pub/linux/kernel/projects/rt/4.%{base_sublevel}/older/patches-4.%{base_sublevel}.%{rt_stable_update}-rt%{rtrelease}.tar.xz
%else
Source1500: https://www.kernel.org/pub/linux/kernel/projects/rt/4.%{base_sublevel}/older/patches-4.%{base_sublevel}-rt%{rtrelease}.tar.xz
%endif
%endif
Source1501: config-fedberry-rt.cfg
# Fix for FIQ issue, see also: https://wiki.linuxfoundation.org/realtime/documentation/known_limitations
Source1502: usb-dwc_otg-fix-system-lockup-when-interrupts-are-threaded.patch

# Sources for kernel-tools
Source2000: cpupower.service
Source2001: cpupower.config

# Here should be only the patches up to the upstream canonical Linus tree.

# For a stable release kernel
%if 0%{?stable_update}
%if 0%{?stable_base}
Source1: https://www.kernel.org/pub/linux/kernel/v4.x/patch-4.%{base_sublevel}.%{stable_base}.xz
%endif

# non-released_kernel case
# These are automagically defined by the rcrev and gitrev values set up
# near the top of this spec file.
%else
%if 0%{?rcrev}
Source1: https://www.kernel.org/pub/linux/kernel/v4.x/patch-4.%{upstream_sublevel}-rc%{rcrev}.xz
%if 0%{?gitrev}
Source2: https://www.kernel.org/pub/linux/kernel/v4.x/patch-4.%{upstream_sublevel}-rc%{rcrev}-git%{gitrev}.xz
%endif
%else
# pre-{base_sublevel+1}-rc1 case
%if 0%{?gitrev}
Source1: https://www.kernel.org/pub/linux/kernel/v4.x/patch-4.%{base_sublevel}-git%{gitrev}.xz
%endif
%endif
%endif

# we also need compile fixes for -vanilla
#Patch04: compile-fixes.patch


%if !%{nopatches}
## Patches for bcm283x builds (append patches with bcm283x)
#script for adding device tree trailer to the kernel img
Patch10: bcm283x-add-mkknlimg-knlinfo.patch

## Patches for bcm270x builds (append patches with bcm270x)
#RasperryPi patch
Patch100: bcm270x-linux-rpi-4.%{base_sublevel}.y-%{rpi_gitshort}.patch.xz

## Patches for both builds (bcm270x & bcm283x)
#FedBerry logo
Patch200: video-logo-fedberry.patch

# END OF PATCH DEFINITIONS
%endif

BuildRoot: %{_tmppath}/kernel-%{KVERREL}-root

%description
The kernel meta package

#
# This macro does requires, provides, conflicts, obsoletes for a kernel package.
#	%%kernel_reqprovconf <subpackage>
# It uses any kernel_<subpackage>_conflicts and kernel_<subpackage>_obsoletes
# macros defined above.
#
%define kernel_reqprovconf \
Provides: kernel = %{rpmversion}-%{pkg_release}\
Provides: kernel-%{_target_cpu} = %{rpmversion}-%{pkg_release}%{?1:+%{1}}\
Provides: kernel-drm-nouveau = 16\
Provides: kernel-uname-r = %{KVERREL}%{?variant}%{?1:+%{1}}\
Requires(pre): %{kernel_prereq}\
Requires(pre): %{initrd_prereq}\
Suggests: linux-firmware\
Requires(pre): bcm283x-firmware\
Requires(pre): raspberrypi-vc-utils\
Requires(preun): systemd\
Conflicts: xorg-x11-drv-vmmouse\
%{expand:%%{?kernel%{?1:_%{1}}_conflicts:Conflicts: %%{kernel%{?1:_%{1}}_conflicts}}}\
%{expand:%%{?kernel%{?1:_%{1}}_obsoletes:Obsoletes: %%{kernel%{?1:_%{1}}_obsoletes}}}\
%{expand:%%{?kernel%{?1:_%{1}}_provides:Provides: %%{kernel%{?1:_%{1}}_provides}}}\
# We can't let RPM do the dependencies automatic because it'll then pick up\
# a correct but undesirable perl dependency from the module headers which\
# isn't required for the kernel proper to function\
AutoReq: no\
AutoProv: yes\
%{nil}

%package headers
Summary: Header files for the Linux kernel for use by glibc
Group: Development/System
Obsoletes: glibc-kernheaders < 3.0-46
Provides: glibc-kernheaders = 3.0-46
%if "0%{?variant}"
Obsoletes: kernel-headers < %{rpmversion}-%{pkg_release}
Provides: kernel-headers = %{rpmversion}-%{pkg_release}
%endif
%description headers
Kernel-headers includes the C header files that specify the interface
between the Linux kernel and userspace libraries and programs.  The
header files define structures and constants that are needed for
building most standard programs and are also needed for rebuilding the
glibc package.

%package debuginfo-common-%{_target_cpu}
Summary: Kernel source files used by %{name}-debuginfo packages
Group: Development/Debug
%description debuginfo-common-%{_target_cpu}
This package is required by %{name}-debuginfo subpackages.
It provides the kernel source files common to all builds.

%if %{with_perf}
%package -n perf
Summary: Performance monitoring for the Linux kernel
Group: Development/System
License: GPLv2
%description -n perf
This package contains the perf tool, which enables performance monitoring
of the Linux kernel.

%package -n perf-debuginfo
Summary: Debug information for package perf
Group: Development/Debug
Requires: %{name}-debuginfo-common-%{_target_cpu} = %{version}-%{release}
AutoReqProv: no
%description -n perf-debuginfo
This package provides debug information for the perf package.

# Note that this pattern only works right to match the .build-id
# symlinks because of the trailing nonmatching alternation and
# the leading .*, because of find-debuginfo.sh's buggy handling
# of matching the pattern against the symlinks file.
%{expand:%%global debuginfo_args %{?debuginfo_args} -p '.*%%{_bindir}/perf(\.debug)?|.*%%{_libexecdir}/perf-core/.*|.*%%{_libdir}/traceevent/plugins/.*|XXX' -o perf-debuginfo.list}

%package -n python-perf
Summary: Python bindings for apps which will manipulate perf events
Group: Development/Libraries
%description -n python-perf
The python-perf package contains a module that permits applications
written in the Python programming language to use the interface
to manipulate perf events.

%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}

%package -n python-perf-debuginfo
Summary: Debug information for package perf python bindings
Group: Development/Debug
Requires: %{name}-debuginfo-common-%{_target_cpu} = %{version}-%{release}
AutoReqProv: no
%description -n python-perf-debuginfo
This package provides debug information for the perf python bindings.

# the python_sitearch macro should already be defined from above
%{expand:%%global debuginfo_args %{?debuginfo_args} -p '.*%%{python_sitearch}/perf.so(\.debug)?|XXX' -o python-perf-debuginfo.list}


%endif # with_perf

%if %{with_tools}
%package -n kernel-tools
Summary: Assortment of tools for the Linux kernel
Group: Development/System
License: GPLv2
Provides:  cpupowerutils = 1:009-0.6.p1
Obsoletes: cpupowerutils < 1:009-0.6.p1
Provides:  cpufreq-utils = 1:009-0.6.p1
Provides:  cpufrequtils = 1:009-0.6.p1
Obsoletes: cpufreq-utils < 1:009-0.6.p1
Obsoletes: cpufrequtils < 1:009-0.6.p1
Obsoletes: cpuspeed < 1:1.5-16
Requires: kernel-tools-libs = %{version}-%{release}
%description -n kernel-tools
This package contains the tools/ directory from the kernel source
and the supporting documentation.

%package -n kernel-tools-libs
Summary: Libraries for the kernels-tools
Group: Development/System
License: GPLv2
%description -n kernel-tools-libs
This package contains the libraries built from the tools/ directory
from the kernel source.

%package -n kernel-tools-libs-devel
Summary: Assortment of tools for the Linux kernel
Group: Development/System
License: GPLv2
Requires: kernel-tools = %{version}-%{release}
Provides:  cpupowerutils-devel = 1:009-0.6.p1
Obsoletes: cpupowerutils-devel < 1:009-0.6.p1
Requires: kernel-tools-libs = %{version}-%{release}
Provides: kernel-tools-devel
%description -n kernel-tools-libs-devel
This package contains the development files for the tools/ directory from
the kernel source.

%package -n kernel-tools-debuginfo
Summary: Debug information for package kernel-tools
Group: Development/Debug
Requires: %{name}-debuginfo-common-%{_target_cpu} = %{version}-%{release}
AutoReqProv: no
%description -n kernel-tools-debuginfo
This package provides debug information for package kernel-tools.

# Note that this pattern only works right to match the .build-id
# symlinks because of the trailing nonmatching alternation and
# the leading .*, because of find-debuginfo.sh's buggy handling
# of matching the pattern against the symlinks file.
%{expand:%%global debuginfo_args %{?debuginfo_args} -p '.*%%{_bindir}/cpupower(\.debug)?|.*%%{_libdir}/libcpupower.*|.*%%{_bindir}/turbostat(\.debug)?|.*%%{_bindir}/tmon(\.debug)?|XXX' -o kernel-tools-debuginfo.list}

%endif # with_tools


#
# This macro creates a kernel-<subpackage>-debuginfo package.
#	%%kernel_debuginfo_package <subpackage>
#
%define kernel_debuginfo_package() \
%package %{?1:%{1}-}debuginfo\
Summary: Debug information for package %{name}%{?1:-%{1}}\
Group: Development/Debug\
Requires: %{name}-debuginfo-common-%{_target_cpu} = %{version}-%{release}\
Provides: %{name}%{?1:-%{1}}-debuginfo-%{_target_cpu} = %{version}-%{release}\
AutoReqProv: no\
%description %{?1:%{1}-}debuginfo\
This package provides debug information for package %{name}%{?1:-%{1}}.\
This is required to use SystemTap with %{name}%{?1:-%{1}}-%{KVERREL}.\
%{expand:%%global debuginfo_args %{?debuginfo_args} -p '/.*/%%{KVERREL}%{?1:[+]%{1}}/.*|/.*%%{KVERREL}%{?1:\+%{1}}(\.debug)?' -o debuginfo%{?1}.list}\
%{nil}

#
# This macro creates a kernel-<subpackage>-devel package.
#	%%kernel_devel_package <subpackage> <pretty-name>
#
%define kernel_devel_package() \
%package %{?1:%{1}-}devel\
Summary: Development package for building kernel modules to match the %{?2:%{2} }kernel\
Group: System Environment/Kernel\
Provides: kernel%{?1:-%{1}}-devel-%{_target_cpu} = %{version}-%{release}\
Provides: kernel-devel-%{_target_cpu} = %{version}-%{release}%{?1:+%{1}}\
Provides: kernel-devel = %{version}-%{release}%{?1:+%{1}}\
Provides: kernel-devel-uname-r = %{KVERREL}%{?variant}%{?1:+%{1}}\
Provides: installonlypkg(kernel)\
AutoReqProv: no\
Requires(pre): /usr/bin/find\
Requires: perl\
%description %{?1:%{1}-}devel\
This package provides kernel headers and makefiles sufficient to build modules\
against the %{?2:%{2} }kernel package.\
%{nil}

#
# This macro creates a kernel-<subpackage>-modules-extra package.
#	%%kernel_modules_extra_package <subpackage> <pretty-name>
#
%define kernel_modules_extra_package() \
%package %{?1:%{1}-}modules-extra\
Summary: Extra kernel modules to match the %{?2:%{2} }kernel\
Group: System Environment/Kernel\
Provides: kernel%{?1:-%{1}}-modules-extra-%{_target_cpu} = %{version}-%{release}\
Provides: kernel%{?1:-%{1}}-modules-extra-%{_target_cpu} = %{version}-%{release}%{?1:+%{1}}\
Provides: kernel%{?1:-%{1}}-modules-extra = %{version}-%{release}%{?1:+%{1}}\
Provides: installonlypkg(kernel-module)\
Provides: kernel%{?1:-%{1}}-modules-extra-uname-r = %{KVERREL}%{?variant}%{?1:+%{1}}\
Requires: kernel-uname-r = %{KVERREL}%{?variant}%{?1:+%{1}}\
Requires: kernel%{?1:-%{1}}-modules-uname-r = %{KVERREL}%{?variant}%{?1:+%{1}}\
AutoReq: no\
AutoProv: yes\
%description %{?1:%{1}-}modules-extra\
This package provides less commonly used kernel modules for the %{?2:%{2} }kernel package.\
%{nil}

#
# This macro creates a kernel-<subpackage>-modules package.
#	%%kernel_modules_package <subpackage> <pretty-name>
#
%define kernel_modules_package() \
%package %{?1:%{1}-}modules\
Summary: kernel modules to match the %{?2:%{2}-}core kernel\
Group: System Environment/Kernel\
Provides: kernel%{?1:-%{1}}-modules-%{_target_cpu} = %{version}-%{release}\
Provides: kernel-modules-%{_target_cpu} = %{version}-%{release}%{?1:+%{1}}\
Provides: kernel-modules = %{version}-%{release}%{?1:+%{1}}\
Provides: installonlypkg(kernel-module)\
Provides: kernel%{?1:-%{1}}-modules-uname-r = %{KVERREL}%{?variant}%{?1:+%{1}}\
Requires: kernel-uname-r = %{KVERREL}%{?variant}%{?1:+%{1}}\
AutoReq: no\
AutoProv: yes\
%description %{?1:%{1}-}modules\
This package provides commonly used kernel modules for the %{?2:%{2}-}core kernel package.\
%{nil}

#
# this macro creates a kernel-<subpackage> meta package.
#	%%kernel_meta_package <subpackage>
#
%define kernel_meta_package() \
%package %{1}\
summary: kernel meta-package for the %{1} kernel\
group: system environment/kernel\
Requires: kernel-%{1}-core-uname-r = %{KVERREL}%{?variant}+%{1}\
Requires: kernel-%{1}-modules-uname-r = %{KVERREL}%{?variant}+%{1}\
%description %{1}\
The meta-package for the %{1} kernel\
%{nil}

#
# This macro creates a kernel-<subpackage> and its -devel and -debuginfo too.
#	%%define variant_summary The Linux kernel compiled for <configuration>
#	%%kernel_variant_package [-n <pretty-name>] <subpackage>
#
%define kernel_variant_package(n:) \
%package %{?1:%{1}-}core\
Summary: %{variant_summary}\
Group: System Environment/Kernel\
Provides: kernel-%{?1:%{1}-}core-uname-r = %{KVERREL}%{?variant}%{?1:+%{1}}\
%{expand:%%kernel_reqprovconf}\
%if %{?1:1} %{!?1:0} \
%{expand:%%kernel_meta_package %{?1:%{1}}}\
%endif\
%{expand:%%kernel_devel_package %{?1:%{1}} %{!?{-n}:%{1}}%{?{-n}:%{-n*}}}\
%{expand:%%kernel_modules_package %{?1:%{1}} %{!?{-n}:%{1}}%{?{-n}:%{-n*}}}\
%{expand:%%kernel_modules_extra_package %{?1:%{1}} %{!?{-n}:%{1}}%{?{-n}:%{-n*}}}\
%{expand:%%kernel_debuginfo_package %{?1:%{1}}}\
%{nil}

# The main -core package
%if %{bcm270x}
%if %{_target_cpu} == armv7hl
%define variant_summary The Linux kernel for the Raspberry Pi 2/3 Model B
%else
%define variant_summary The Linux kernel for the Raspberry Pi Model A, B & Zero
%endif
%kernel_variant_package 
%description core
This package includes a patched version of the Linux kernel built for
Raspberry Pi devices that use the Broadcom BCM27XX SOC. The
kernel package contains the Linux kernel (vmlinuz), the core of any
Linux operating system.  The kernel handles the basic functions
of the operating system: memory allocation, process allocation, device
input and output, etc.
%else
%define variant_summary The Linux kernel
%kernel_variant_package 
%description core
The kernel package contains the Linux kernel (vmlinuz), the core of any
Linux operating system.  The kernel handles the basic functions
of the operating system: memory allocation, process allocation, device
input and output, etc.
%endif

%prep

%if "%{baserelease}" == "0"
echo "baserelease must be greater than zero"
exit 1
%endif

# more sanity checking; do it quietly
if [ "%{patches}" != "%%{patches}" ] ; then
  for patch in %{patches} ; do
    if [ ! -f $patch ] ; then
      echo "ERROR: Patch  ${patch##/*/}  listed in specfile but is missing"
      exit 1
    fi
  done
fi 2>/dev/null

patch_command='patch -p1 -F1 -s'
ApplyPatch()
{
  local patch=$1
  shift
  if [ ! -f $patch ]; then
    exit 1
  fi
  case "$patch" in
  *.bz2) bunzip2 < "$patch" | $patch_command ${1+"$@"} ;;
  *.gz)  gunzip  < "$patch" | $patch_command ${1+"$@"} ;;
  *.xz)  unxz    < "$patch" | $patch_command ${1+"$@"} ;;
  *) $patch_command ${1+"$@"} < "$patch" ;;
  esac
}

# don't apply patch if it's empty
ApplyOptionalPatch()
{
  local patch=$1
  shift
  if [ ! -f $patch ]; then
    exit 1
  fi
  local C=$(wc -l $patch | awk '{print $1}')
  if [ "$C" -gt 9 ]; then
    ApplyPatch $patch ${1+"$@"}
  fi
}

# First we unpack the kernel tarball.
# If this isn't the first make prep, we use links to the existing clean tarball
# which speeds things up quite a bit.

# Update to latest upstream.
%if 0%{?released_kernel}
%define vanillaversion 4.%{base_sublevel}
# non-released_kernel case
%else
%if 0%{?rcrev}
%define vanillaversion 4.%{upstream_sublevel}-rc%{rcrev}
%if 0%{?gitrev}
%define vanillaversion 4.%{upstream_sublevel}-rc%{rcrev}-git%{gitrev}
%endif
%else
# pre-{base_sublevel+1}-rc1 case
%if 0%{?gitrev}
%define vanillaversion 4.%{base_sublevel}-git%{gitrev}
%else
%define vanillaversion 4.%{base_sublevel}
%endif
%endif
%endif

# %%{vanillaversion} : the full version name, e.g. 2.6.35-rc6-git3
# %%{kversion}       : the base version, e.g. 2.6.34

# Use kernel-%%{kversion}%%{?dist} as the top-level directory name
# so we can prep different trees within a single git directory.

# Build a list of the other top-level kernel tree directories.
# This will be used to hardlink identical vanilla subdirs.
sharedirs=$(find "$PWD" -maxdepth 1 -type d -name 'kernel-4.*' \
            | grep -x -v "$PWD"/kernel-%{kversion}%{?dist}) ||:

# Delete all old stale trees.
if [ -d kernel-%{kversion}%{?dist} ]; then
  cd kernel-%{kversion}%{?dist}
  for i in linux-*
  do
     if [ -d $i ]; then
       # Just in case we ctrl-c'd a prep already
       rm -rf deleteme.%{_target_cpu}
       # Move away the stale away, and delete in background.
       mv $i deleteme-$i
       rm -rf deleteme* &
     fi
  done
  cd ..
fi

# Generate new tree
if [ ! -d kernel-%{kversion}%{?dist}/vanilla-%{vanillaversion} ]; then

  if [ -d kernel-%{kversion}%{?dist}/vanilla-%{kversion} ]; then

    # The base vanilla version already exists.
    cd kernel-%{kversion}%{?dist}

    # Any vanilla-* directories other than the base one are stale.
    for dir in vanilla-*; do
      [ "$dir" = vanilla-%{kversion} ] || rm -rf $dir &
    done

  else

    rm -f pax_global_header
    # Look for an identical base vanilla dir that can be hardlinked.
    for sharedir in $sharedirs ; do
      if [[ ! -z $sharedir  &&  -d $sharedir/vanilla-%{kversion} ]] ; then
        break
      fi
    done
    if [[ ! -z $sharedir  &&  -d $sharedir/vanilla-%{kversion} ]] ; then
%setup -q -n kernel-%{kversion}%{?dist} -c -T
      cp -al $sharedir/vanilla-%{kversion} .
    else
%setup -q -n kernel-%{kversion}%{?dist} -c
      mv linux-%{kversion} vanilla-%{kversion}
    fi

  fi

%if "%{kversion}" != "%{vanillaversion}"

  for sharedir in $sharedirs ; do
    if [[ ! -z $sharedir  &&  -d $sharedir/vanilla-%{vanillaversion} ]] ; then
      break
    fi
  done
  if [[ ! -z $sharedir  &&  -d $sharedir/vanilla-%{vanillaversion} ]] ; then

    cp -al $sharedir/vanilla-%{vanillaversion} .

  else

    # Need to apply patches to the base vanilla version.
    cp -al vanilla-%{kversion} vanilla-%{vanillaversion}
    cd vanilla-%{vanillaversion}

# Update vanilla to the latest upstream.
# (non-released_kernel case only)
%if 0%{?rcrev}
    xzcat %{SOURCE1} | patch -p1 -F1 -s
%if 0%{?gitrev}
    xzcat %{SOURCE2} | patch -p1 -F1 -s
%endif
%else
# pre-{base_sublevel+1}-rc1 case
%if 0%{?gitrev}
    xzcat %{SOURCE1} | patch -p1 -F1 -s
%endif
%endif

    cd ..

  fi

%endif

else

  # We already have all vanilla dirs, just change to the top-level directory.
  cd kernel-%{kversion}%{?dist}

fi

# Now build the fedora kernel tree.
cp -al vanilla-%{vanillaversion} linux-%{KVERREL}

cd linux-%{KVERREL}

# released_kernel with possible stable updates
%if 0%{?stable_base}
# This is special because the kernel spec is HELL and nothing is consistent
xzcat %{SOURCE1} | patch -p1 -F1 -s
%endif

#
# misc small stuff to make things compile
#
#ApplyOptionalPatch compile-fixes.patch

%if !%{nopatches}

for i in %{patches}; do
%if !%{bcm270x}
    if [ ! $(echo $i |grep "/bcm270x") ]; then
        ApplyPatch $i
    fi
%endif

%if %{bcm270x}
    if [ ! $(echo $i |grep "/bcm283x") ]; then
        ApplyPatch $i
    fi
%endif
done

%if %{enable_preempt}
%if %{with_rt_preempt}
# apply rt kernel patches
unxz -c %{SOURCE1500} | tar -xf - -C .
# we don't want to use the localversion.patch
sed -i 's/\(localversion.patch\)/# \1/g' patches/series
quilt push -a
patch -p1 < %{SOURCE1502}
%endif
%endif

# END OF PATCH APPLICATIONS
%endif

# Any further pre-build tree manipulations happen here.

chmod +x scripts/checkpatch.pl

# This Prevents scripts/setlocalversion from mucking with our version numbers.
touch .scmversion

%define make make %{?cross_opts}

# get rid of unwanted files resulting from patch fuzz
find . \( -name "*.orig" -o -name "*~" \) -exec rm -f {} \; >/dev/null

# remove unnecessary SCM files
find . -name .gitignore -exec rm -f {} \; >/dev/null

cd ..

###
### build
###
%build

%ifnarch %{arm}
echo "This build is for arm archiecture only"
exit 1
%endif

%if %{with_debuginfo}
# This override tweaks the kernel makefiles so that we run debugedit on an
# object before embedding it.  When we later run find-debuginfo.sh, it will
# run debugedit again.  The edits it does change the build ID bits embedded
# in the stripped object, but repeating debugedit is a no-op.  We do it
# beforehand to get the proper final build ID bits into the embedded image.
# This affects the vDSO images in vmlinux, and the vmlinux image in bzImage.
export AFTER_LINK=\
'sh -xc "/usr/lib/rpm/debugedit -b $$RPM_BUILD_DIR -d /usr/src/debug \
    				-i $@ > $@.id"'
%endif

cp_vmlinux()
{
  eu-strip --remove-comment -o "$2" "$1"
}

BuildKernel() {
    MakeTarget=$1
    KernelImage=$2
    Flavour=$3
    Arch=%{asmarch}
    Flav=${Flavour:++${Flavour}}
    InstallName=${4:-vmlinuz}
    DevelDir=/usr/src/kernels/%{KVERREL}

    # When the bootable image is just the ELF kernel, strip it.
    # We already copy the unstripped file into the debuginfo package.
    if [ "$KernelImage" = vmlinux ]; then
      CopyKernel=cp_vmlinux
    else
      CopyKernel=cp
    fi

    #KernelVer=%{version}-%{release}.%{_target_cpu}${Flav}
    KernelVer=%{version}-%{release}.%{_target_cpu}
    echo BUILDING A KERNEL FOR ${Flavour} %{_target_cpu}...

    %if 0%{?stable_update}
    # make sure SUBLEVEL is incremented on a stable release.
    perl -p -i -e "s/^SUBLEVEL.*/SUBLEVEL = %{?stablerev}/" Makefile
    %endif

    # make sure EXTRAVERSION says what we want it to say
    perl -p -i -e "s/^EXTRAVERSION.*/EXTRAVERSION = -%{release}.%{_target_cpu}/" Makefile

    # if pre-rc1 devel kernel, must fix up PATCHLEVEL for our versioning scheme
    %if !0%{?rcrev}
    %if 0%{?gitrev}
    perl -p -i -e 's/^PATCHLEVEL.*/PATCHLEVEL = %{upstream_sublevel}/' Makefile
    %endif
    %endif

    # and now to start the build process
    make -s mrproper
    %if !%{bcm270x}
    make multi_v7_defconfig
    # merge fedberry kernel config fragments
    scripts/kconfig/merge_config.sh -m -r .config %{SOURCE1100}
    %endif
    %if %{bcm270x}
    %if %{_target_cpu} == armv7hl
    make bcm2709_defconfig
    %else
    make bcmrpi_defconfig
    %endif
    # merge fedberry kernel config fragments
    scripts/kconfig/merge_config.sh -m -r .config %{SOURCE1000}
    %endif

    %if %{enable_preempt}
    %if %{with_rt_preempt}
    # merge rt-preempt kernel config changes
    scripts/kconfig/merge_config.sh -m -r .config %{SOURCE1501}
    %endif
    %endif

    %if %{with_lpae}
    sed -i 's/# CONFIG_ARM_LPAE is not set/CONFIG_ARM_LPAE=y/' .config
    sed -i 's/# CONFIG_ARCH_PHYS_ADDR_T_64BIT is not set/CONFIG_ARCH_PHYS_ADDR_T_64BIT=y/' .config
    sed -i 's/CONFIG_VMSPLIT_2G=y/# CONFIG_VMSPLIT_2G is not set/' .config
    sed -i 's/# CONFIG_VMSPLIT_3G is not set/CONFIG_VMSPLIT_3G=y/' .config
    %endif

    echo USING ARCH=$Arch
    #make ARCH=$Arch oldnoconfig >/dev/null
    make ARCH=$Arch oldconfig
    %{make} ARCH=$Arch %{?_smp_mflags} $MakeTarget %{?sparse_mflags} %{?kernel_mflags}
    %{make} ARCH=$Arch %{?_smp_mflags} modules %{?sparse_mflags} || exit 1

    # Start installing the results
    %if %{with_debuginfo}
    mkdir -p $RPM_BUILD_ROOT%{debuginfodir}/boot
    mkdir -p $RPM_BUILD_ROOT%{debuginfodir}/%{image_install_path}
    %endif
    mkdir -p $RPM_BUILD_ROOT/%{image_install_path}
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer

    # Device Tree / Overlay
    %{make} ARCH=$Arch dtbs dtbs_install INSTALL_DTBS_PATH=$RPM_BUILD_ROOT/%{image_install_path}/dtb-$KernelVer
    cp -r $RPM_BUILD_ROOT/%{image_install_path}/dtb-$KernelVer $RPM_BUILD_ROOT/lib/modules/$KernelVer/dtb
    %if %{bcm270x}
    cp -p arch/$Arch/boot/dts/overlays/README $RPM_BUILD_ROOT/lib/modules/$KernelVer/dtb/overlays/
    mkdir -p $RPM_BUILD_ROOT/%{image_install_path}/overlays
    %endif

    # Start installing the results
    install -m 644 .config $RPM_BUILD_ROOT/boot/config-$KernelVer
    install -m 644 .config $RPM_BUILD_ROOT/lib/modules/$KernelVer/config
    install -m 644 System.map $RPM_BUILD_ROOT/boot/System.map-$KernelVer
    install -m 644 System.map $RPM_BUILD_ROOT/lib/modules/$KernelVer/System.map

    # We estimate the size of the initramfs because rpm needs to take this size
    # into consideration when performing disk space calculations. (See bz #530778)
    dd if=/dev/zero of=$RPM_BUILD_ROOT/boot/initramfs-$KernelVer.img bs=1M count=20

    # add the device tree trailer to the kernel img
    chmod +x scripts/mkknlimg
    %if !%{bcm270x}
    scripts/mkknlimg --dtok --283x $KernelImage $RPM_BUILD_ROOT/%{image_install_path}/$InstallName-$KernelVer
    %else
    scripts/mkknlimg --dtok --270x $KernelImage $RPM_BUILD_ROOT/%{image_install_path}/$InstallName-$KernelVer
    %endif
    chmod 755 $RPM_BUILD_ROOT/%{image_install_path}/$InstallName-$KernelVer
    cp $RPM_BUILD_ROOT/%{image_install_path}/$InstallName-$KernelVer $RPM_BUILD_ROOT/lib/modules/$KernelVer/$InstallName

    # hmac sign the kernel for FIPS
    echo "Creating hmac file: $RPM_BUILD_ROOT/%{image_install_path}/.vmlinuz-$KernelVer.hmac"
    ls -l $RPM_BUILD_ROOT/%{image_install_path}/$InstallName-$KernelVer
    sha512hmac $RPM_BUILD_ROOT/%{image_install_path}/$InstallName-$KernelVer | sed -e "s,$RPM_BUILD_ROOT,," > $RPM_BUILD_ROOT/%{image_install_path}/.vmlinuz-$KernelVer.hmac;
    cp $RPM_BUILD_ROOT/%{image_install_path}/.vmlinuz-$KernelVer.hmac $RPM_BUILD_ROOT/lib/modules/$KernelVer/.vmlinuz.hmac

    mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer
    # Override $(mod-fw) because we don't want it to install any firmware
    # we'll get it from the linux-firmware package and we don't want conflicts
    %{make} ARCH=$Arch INSTALL_MOD_PATH=$RPM_BUILD_ROOT modules_install KERNELRELEASE=$KernelVer mod-fw=

    # And save the headers/makefiles etc for building modules against
    #
    # This all looks scary, but the end result is supposed to be:
    # * all arch relevant include/ files
    # * all Makefile/Kconfig files
    # * all script/ files

    rm -f $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    rm -f $RPM_BUILD_ROOT/lib/modules/$KernelVer/source
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    (cd $RPM_BUILD_ROOT/lib/modules/$KernelVer ; ln -s build source)
    # dirs for additional modules per module-init-tools, kbuild/modules.txt
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer/extra
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer/updates
    # first copy everything
    cp --parents `find  -type f -name "Makefile*" -o -name "Kconfig*"` $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp Module.symvers $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp System.map $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    if [ -s Module.markers ]; then
      cp Module.markers $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    fi
    # then drop all but the needed Makefiles/Kconfig files
    rm -rf $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/Documentation
    rm -rf $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/scripts
    rm -rf $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/include
    cp .config $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp -a scripts $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    if [ -d arch/$Arch/scripts ]; then
      cp -a arch/$Arch/scripts $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/arch/%{_arch} || :
    fi
    if [ -f arch/$Arch/*lds ]; then
      cp -a arch/$Arch/*lds $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/arch/%{_arch}/ || :
    fi
    rm -f $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/scripts/*.o
    rm -f $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/scripts/*/*.o
    if [ -d arch/%{asmarch}/include ]; then
      cp -a --parents arch/%{asmarch}/include $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    fi

    # include the machine specific headers
    if [ -d arch/%{asmarch}/mach-${Flavour}/include ]; then
      cp -a --parents arch/%{asmarch}/mach-${Flavour}/include $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    fi

    # include a few files for 'make prepare'
    cp -a --parents arch/arm/tools/gen-mach-types $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/arm/tools/mach-types $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/

    cp -a include $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/include

    # Make sure the Makefile and version.h have a matching timestamp so that
    # external modules can be built
    touch -r $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/Makefile $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/include/generated/uapi/linux/version.h

    # Copy .config to include/config/auto.conf so "make prepare" is unnecessary.
    cp $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/.config $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/include/config/auto.conf

%if %{with_debuginfo}
    if test -s vmlinux.id; then
      cp vmlinux.id $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/vmlinux.id
    else
      echo >&2 "*** ERROR *** no vmlinux build ID! ***"
      exit 1
    fi

    #
    # save the vmlinux file for kernel debugging into the kernel-debuginfo rpm
    #
    mkdir -p $RPM_BUILD_ROOT%{debuginfodir}/lib/modules/$KernelVer
    cp vmlinux $RPM_BUILD_ROOT%{debuginfodir}/lib/modules/$KernelVer
%endif

    find $RPM_BUILD_ROOT/lib/modules/$KernelVer -name "*.ko" -type f >modnames

    # mark modules executable so that strip-to-file can strip them
    xargs --no-run-if-empty chmod u+x < modnames

    # Generate a list of modules for block and networking.

    grep -F /drivers/ modnames | xargs --no-run-if-empty nm -upA |
    sed -n 's,^.*/\([^/]*\.ko\):  *U \(.*\)$,\1 \2,p' > drivers.undef

    collect_modules_list()
    {
      sed -r -n -e "s/^([^ ]+) \\.?($2)\$/\\1/p" drivers.undef |
        LC_ALL=C sort -u > $RPM_BUILD_ROOT/lib/modules/$KernelVer/modules.$1
      if [ ! -z "$3" ]; then
        sed -r -e "/^($3)\$/d" -i $RPM_BUILD_ROOT/lib/modules/$KernelVer/modules.$1
      fi
    }

    collect_modules_list networking \
    			 'register_netdev|ieee80211_register_hw|usbnet_probe|phy_driver_register|rt(l_|2x00)(pci|usb)_probe|register_netdevice'
    collect_modules_list block \
    			 'ata_scsi_ioctl|scsi_add_host|scsi_add_host_with_dma|blk_alloc_queue|blk_init_queue|register_mtd_blktrans|scsi_esp_register|scsi_register_device_handler|blk_queue_physical_block_size' 'pktcdvd.ko|dm-mod.ko'
    collect_modules_list drm \
    			 'drm_open|drm_init'
    collect_modules_list modesetting \
    			 'drm_crtc_init'

    # detect missing or incorrect license tags
    ( find $RPM_BUILD_ROOT/lib/modules/$KernelVer -name '*.ko' | xargs /sbin/modinfo -l | \
        grep -E -v 'GPL( v2)?$|Dual BSD/GPL$|Dual MPL/GPL$|GPL and additional rights$' ) && exit 1

    # remove files that will be auto generated by depmod at rpm -i time
    pushd $RPM_BUILD_ROOT/lib/modules/$KernelVer/
        rm -f modules.{alias*,builtin.bin,dep*,*map,symbols*,devname,softdep}
    popd

    # Call the modules-extra script to move things around
    %{SOURCE17} $RPM_BUILD_ROOT/lib/modules/$KernelVer %{SOURCE16}

    #
    # Generate the kernel-core and kernel-modules files lists
    #

    # Copy the System.map file for depmod to use, and create a backup of the
    # full module tree so we can restore it after we're done filtering
    cp System.map $RPM_BUILD_ROOT/.
    pushd $RPM_BUILD_ROOT
    mkdir restore
    cp -r lib/modules/$KernelVer/* restore/.

    # don't include anything going into k-m-e in the file lists
    rm -rf lib/modules/$KernelVer/extra

    # Find all the module files and filter them out into the core and modules
    # lists.  This actually removes anything going into -modules from the dir.
    find lib/modules/$KernelVer/kernel -name *.ko | sort -n > modules.list
	cp $RPM_SOURCE_DIR/filter-*.sh .
    %{SOURCE99} modules.list %{_target_cpu}
	rm filter-*.sh

    # Run depmod on the resulting module tree and make sure it isn't broken
    depmod -b . -aeF ./System.map $KernelVer &> depmod.out
    if [ -s depmod.out ]; then
        echo "Depmod failure"
        cat depmod.out
        exit 1
    else
        rm depmod.out
    fi
    # remove files that will be auto generated by depmod at rpm -i time
    pushd $RPM_BUILD_ROOT/lib/modules/$KernelVer/
        rm -f modules.{alias*,builtin.bin,dep*,*map,symbols*,devname,softdep}
    popd

    # Go back and find all of the various directories in the tree.  We use this
    # for the dir lists in kernel-core
    find lib/modules/$KernelVer/kernel -type d | sort -n > module-dirs.list

    # Cleanup
    rm System.map
    cp -r restore/* lib/modules/$KernelVer/.
    rm -rf restore
    popd

    # Make sure the files lists start with absolute paths or rpmbuild fails.
    # Also add in the dir entries
    sed -e 's/^lib*/\/lib/' %{?zipsed} $RPM_BUILD_ROOT/k-d.list > ../kernel-modules.list
    sed -e 's/^lib*/%dir \/lib/' %{?zipsed} $RPM_BUILD_ROOT/module-dirs.list > ../kernel-core.list
    sed -e 's/^lib*/\/lib/' %{?zipsed} $RPM_BUILD_ROOT/modules.list >> ../kernel-core.list

    # Cleanup
    rm -f $RPM_BUILD_ROOT/k-d.list
    rm -f $RPM_BUILD_ROOT/modules.list
    rm -f $RPM_BUILD_ROOT/module-dirs.list

    # Move the devel headers out of the root file system
    mkdir -p $RPM_BUILD_ROOT/usr/src/kernels
    mv $RPM_BUILD_ROOT/lib/modules/$KernelVer/build $RPM_BUILD_ROOT/$DevelDir

    # This is going to create a broken link during the build, but we don't use
    # it after this point.  We need the link to actually point to something
    # when kernel-devel is installed, and a relative link doesn't work across
    # the F17 UsrMove feature.
    ln -sf $DevelDir $RPM_BUILD_ROOT/lib/modules/$KernelVer/build

    # prune junk from kernel-devel
    find $RPM_BUILD_ROOT/usr/src/kernels -name ".*.cmd" -exec rm -f {} \;
}

###
# DO it...
###

# prepare directories
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/boot
mkdir -p $RPM_BUILD_ROOT%{_libexecdir}

cd linux-%{KVERREL}

BuildKernel %make_target %kernel_image %{?Flavour}

%global perf_make \
  make %{?cross_opts} %{?_smp_mflags} -C tools/perf WERROR=0 NO_LIBUNWIND=1 HAVE_CPLUS_DEMANGLE=1 NO_GTK2=1 NO_STRLCPY=1 NO_BIONIC=1 prefix=%{_prefix}
%if %{with_perf}
# perf
%{perf_make} DESTDIR=$RPM_BUILD_ROOT all
%endif

%if %{with_tools}
# cpupower
# make sure version-gen.sh is executable.
chmod +x tools/power/cpupower/utils/version-gen.sh
%{make} %{?_smp_mflags} -C tools/power/cpupower CPUFREQ_BENCH=false
pushd tools/thermal/tmon/
%{make}
popd
pushd tools/iio/
%{make}
popd
pushd tools/gpio/
%{make}
popd
pushd tools/kvm/kvm_stat
%{make}
popd
%endif


###
### Special hacks for debuginfo subpackages.
###

# This macro is used by %%install, so we must redefine it before that.
%define debug_package %{nil}

%if %{with_debuginfo}

%define __debug_install_post \
  /usr/lib/rpm/find-debuginfo.sh %{debuginfo_args} %{_builddir}/%{?buildsubdir}\
%{nil}

%ifnarch noarch
%global __debug_package 1
%files -f debugfiles.list debuginfo-common-%{_target_cpu}
%defattr(-,root,root)
%endif

%endif

#
# Disgusting hack alert! We need to ensure we sign modules *after* all
# invocations of strip occur, which is in __debug_install_post if
# find-debuginfo.sh runs, and __os_install_post if not.
#
%define __spec_install_post \
  %{?__debug_package:%{__debug_install_post}}\
  %{__arch_install_post}\
  %{__os_install_post}


###
### install
###

%install

cd linux-%{KVERREL}

# We have to do the headers install before the tools install because the
# kernel headers_install will remove any header files in /usr/include that
# it doesn't install itself.

%if %{with_headers}
# Install kernel headers
make ARCH=%{hdrarch} INSTALL_HDR_PATH=$RPM_BUILD_ROOT/usr headers_install

find $RPM_BUILD_ROOT/usr/include \
     \( -name .install -o -name .check -o \
     	-name ..install.cmd -o -name ..check.cmd \) | xargs rm -f

%endif

%if %{with_perf}
# perf tool binary and supporting scripts/binaries
%{perf_make} DESTDIR=$RPM_BUILD_ROOT lib=%{_lib} install-bin install-traceevent-plugins
# remove the 'trace' symlink.
rm -f %{buildroot}%{_bindir}/trace

# python-perf extension
%{perf_make} DESTDIR=$RPM_BUILD_ROOT install-python_ext

# perf man pages (note: implicit rpm magic compresses them later)
mkdir -p %{buildroot}/%{_mandir}/man1
pushd %{buildroot}/%{_mandir}/man1
tar -xf %{SOURCE10}
%if !%{with_tools}
    rm -f kvm_stat.1
%endif
popd

# remove perf-tips dir
rm -rf %{buildroot}%{_docdir}/perf-tip
%endif

%if %{with_tools}
%{make} -C tools/power/cpupower DESTDIR=$RPM_BUILD_ROOT libdir=%{_libdir} mandir=%{_mandir} CPUFREQ_BENCH=false install
rm -f %{buildroot}%{_libdir}/*.{a,la}
%find_lang cpupower
mv cpupower.lang ../
chmod 0755 %{buildroot}%{_libdir}/libcpupower.so*
mkdir -p %{buildroot}%{_unitdir} %{buildroot}%{_sysconfdir}/sysconfig
install -m644 %{SOURCE2000} %{buildroot}%{_unitdir}/cpupower.service
install -m644 %{SOURCE2001} %{buildroot}%{_sysconfdir}/sysconfig/cpupower
pushd tools/thermal/tmon
make INSTALL_ROOT=%{buildroot} install
popd
pushd tools/iio
make INSTALL_ROOT=%{buildroot} install
popd
pushd tools/gpio
make DESTDIR=%{buildroot} install
popd
pushd tools/kvm/kvm_stat
make INSTALL_ROOT=%{buildroot} install-tools
popd
%endif


###
### clean
###

%clean
rm -rf $RPM_BUILD_ROOT

###
### scripts
###

%if %{with_tools}
%post -n kernel-tools
/sbin/ldconfig

%postun -n kernel-tools
/sbin/ldconfig
%endif

#
# This macro defines a %%post script for a kernel*-devel package.
#	%%kernel_devel_post [<subpackage>]
#
%define kernel_devel_post() \
%{expand:%%post %{?1:%{1}-}devel}\
if [ -f /etc/sysconfig/kernel ]\
then\
    . /etc/sysconfig/kernel || exit $?\
fi\
if [ "$HARDLINK" != "no" -a -x /usr/sbin/hardlink ]\
then\
    (cd /usr/src/kernels/%{KVERREL}%{?1:+%{1}} &&\
     /usr/bin/find . -type f | while read f; do\
       hardlink -c /usr/src/kernels/*.fc*.*/$f $f\
     done)\
fi\
%{nil}

#
# This macro defines a %%post script for a kernel*-modules-extra package.
# It also defines a %%postun script that does the same thing.
#	%%kernel_modules_extra_post [<subpackage>]
#
%define kernel_modules_extra_post() \
%{expand:%%post %{?1:%{1}-}modules-extra}\
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
%{nil}\
%{expand:%%postun %{?1:%{1}-}modules-extra}\
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
%{nil}

#
# This macro defines a %%post script for a kernel*-modules package.
# It also defines a %%postun script that does the same thing.
#	%%kernel_modules_post [<subpackage>]
#
%define kernel_modules_post() \
%{expand:%%post %{?1:%{1}-}modules}\
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
%{nil}\
%{expand:%%postun %{?1:%{1}-}modules}\
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
%{nil}

# This macro defines a %%posttrans script for a kernel package.
#	%%kernel_variant_posttrans [<subpackage>]
# More text can follow to go at the end of this variant's %%post.
#
%define kernel_variant_posttrans() \
%{expand:%%posttrans %{?1:%{1}-}core}\
/sbin/new-kernel-pkg --package kernel --rpmposttrans %{KVERREL}%{?1:+%{1}} || exit $?\
%if %{_target_cpu} == armv7hl\
cp -f /lib/modules/%{KVERREL}%{?1:+%{1}}/vmlinuz /%{image_install_path}/kernel7.img\
%else\
cp -f /lib/modules/%{KVERREL}%{?1:+%{1}}/vmlinuz /%{image_install_path}/kernel.img\
%endif\
cp -f /lib/modules/%{KVERREL}%{?1:+%{1}}/vmlinuz /%{image_install_path}/vmlinuz-%{KVERREL}%{?1:+%{1}}\
%if %{bcm270x}\
rm -f /boot/overlays/*\
mkdir -p /boot/overlays\
cp -f /lib/modules/%{KVERREL}%{?1:+%{1}}/dtb/overlays/* /boot/overlays/\
%if %{_target_cpu} == armv7hl\
cp -f /lib/modules/%{KVERREL}%{?1:+%{1}}/dtb/bcm2709* /boot/\
cp -f /lib/modules/%{KVERREL}%{?1:+%{1}}/dtb/bcm2710* /boot/\
%else\
cp -f /lib/modules/%{KVERREL}%{?1:+%{1}}/dtb/bcm2708* /boot/\
%endif\
%else\
cp -f /lib/modules/%{KVERREL}%{?1:+%{1}}/dtb/bcm28* /boot/\
%endif\
cp -f /lib/modules/%{KVERREL}%{?1:+%{1}}/config /%{image_install_path}/config-%{KVERREL}%{?1:+%{1}}\
cp -f /lib/modules/%{KVERREL}%{?1:+%{1}}/System.map /%{image_install_path}/System.map-%{KVERREL}%{?1:+%{1}}\
cp -f /lib/modules/%{KVERREL}%{?1:+%{1}}/.vmlinuz.hmac /%{image_install_path}/.vmlinuz.hmac-%{KVERREL}%{?1:+%{1}}\
%{nil}

#
# This macro defines a %%post script for a kernel package and its devel package.
#	%%kernel_variant_post [-v <subpackage>] [-r <replace>]
# More text can follow to go at the end of this variant's %%post.
#
%define kernel_variant_post(v:r:) \
%{expand:%%kernel_devel_post %{?-v*}}\
%{expand:%%kernel_modules_post %{?-v*}}\
%{expand:%%kernel_modules_extra_post %{?-v*}}\
%{expand:%%kernel_variant_posttrans %{?-v*}}\
%{expand:%%post %{?-v*:%{-v*}-}core}\
%{nil}

#
# This macro defines a %%preun script for a kernel package.
#	%%kernel_variant_preun <subpackage>
#
%define kernel_variant_preun() \
%{expand:%%preun %{?1:%{1}-}core}\
/bin/kernel-install remove %{KVERREL}%{?1:+%{1}} /%{image_install_path}/vmlinuz-%{KVERREL}%{?1:+%{1}} || exit $?\
rm -f /%{image_install_path}/.vmlinuz.hmac-%{KVERREL}%{?1:+%{1}}\
%{nil}

%kernel_variant_preun
%kernel_variant_post -r kernel

if [ -x /sbin/ldconfig ]
then
    /sbin/ldconfig -X || exit $?
fi

###
### file lists
###

%if %{with_headers}
%files headers
%defattr(-,root,root)
/usr/include/*
%endif

%if %{with_perf}
%files -n perf
%defattr(-,root,root)
%{_bindir}/perf
%dir %{_libdir}/traceevent/plugins
%{_libdir}/traceevent/plugins/*
%dir %{_libexecdir}/perf-core
%{_libexecdir}/perf-core/*
%{_datadir}/perf-core/*
%{_mandir}/man[1-8]/perf*
%{_sysconfdir}/bash_completion.d/perf
%doc linux-%{KVERREL}/tools/perf/Documentation/examples.txt
%doc linux-%{KVERREL}/tools/perf/Documentation/tips.txt

%files -n python-perf
%defattr(-,root,root)
%{python_sitearch}

%if %{with_debuginfo}
%files -f perf-debuginfo.list -n perf-debuginfo
%defattr(-,root,root)

%files -f python-perf-debuginfo.list -n python-perf-debuginfo
%defattr(-,root,root)
%endif
%endif # with_perf

%if %{with_tools}
%files -n kernel-tools -f cpupower.lang
%defattr(-,root,root)
%{_bindir}/cpupower
%{_unitdir}/cpupower.service
%{_mandir}/man[1-8]/cpupower*
%config(noreplace) %{_sysconfdir}/sysconfig/cpupower
%{_bindir}/tmon
%{_bindir}/iio_event_monitor
%{_bindir}/iio_generic_buffer
%{_bindir}/lsiio
%{_bindir}/lsgpio
%{_bindir}/gpio-hammer
%{_bindir}/gpio-event-mon
%{_mandir}/man1/kvm_stat*
%{_bindir}/kvm_stat


%if %{with_debuginfo}
%files -f kernel-tools-debuginfo.list -n kernel-tools-debuginfo
%defattr(-,root,root)
%endif

%files -n kernel-tools-libs
%{_libdir}/libcpupower.so.0
%{_libdir}/libcpupower.so.0.0.1

%files -n kernel-tools-libs-devel
%{_libdir}/libcpupower.so
%{_includedir}/cpufreq.h
%endif # with_perf

# empty meta-package
%files
%defattr(-,root,root)

# This is %%{image_install_path} on an arch where that includes ELF files,
# or empty otherwise.
%define elf_image_install_path %{?kernel_image_elf:%{image_install_path}}

#
# This macro defines the %%files sections for a kernel package
# and its devel and debuginfo packages.
#	%%kernel_variant_files [-k vmlinux] <condition> <subpackage>
#
%define kernel_variant_files(k:) \
%{expand:%%files -f kernel-%{?2:%{2}-}core.list %{?2:%{2}-}core}\
%defattr(-,root,root)\
%{!?_licensedir:%global license %%doc}\
%license linux-%{KVERREL}/COPYING\
%ghost /%{image_install_path}/%{?-k:%{-k*}}%{!?-k:vmlinuz}-%{KVERREL}%{?2:+%{2}}\
/lib/modules/%{KVERREL}%{?2:+%{2}}/.vmlinuz.hmac\
%ghost /%{image_install_path}/.vmlinuz-%{KVERREL}%{?2:+%{2}}.hmac\
/lib/modules/%{KVERREL}%{?2:+%{2}}/dtb\
%ghost /%{image_install_path}/dtb-%{KVERREL}%{?2:+%{2}}\
/lib/modules/%{KVERREL}%{?2:+%{2}}/%{?-k:%{-k*}}%{!?-k:vmlinuz}\
%attr(600,root,root) /lib/modules/%{KVERREL}%{?2:+%{2}}/System.map\
%ghost /boot/System.map-%{KVERREL}%{?2:+%{2}}\
/lib/modules/%{KVERREL}%{?2:+%{2}}/config\
%ghost /boot/config-%{KVERREL}%{?2:+%{2}}\
%ghost /boot/initramfs-%{KVERREL}%{?2:+%{2}}.img\
%{?_bcm270x:%ghost /%{image_install_path}/overlays}\
%dir /lib/modules\
%dir /lib/modules/%{KVERREL}%{?2:+%{2}}\
%dir /lib/modules/%{KVERREL}%{?2:+%{2}}/kernel\
/lib/modules/%{KVERREL}%{?2:+%{2}}/build\
/lib/modules/%{KVERREL}%{?2:+%{2}}/source\
/lib/modules/%{KVERREL}%{?2:+%{2}}/updates\
/lib/modules/%{KVERREL}%{?2:+%{2}}/modules.*\
%{expand:%%files -f kernel-%{?2:%{2}-}modules.list %{?2:%{2}-}modules}\
%defattr(-,root,root)\
%{expand:%%files %{?2:%{2}-}devel}\
%defattr(-,root,root)\
/usr/src/kernels/%{KVERREL}%{?2:+%{2}}\
%{expand:%%files %{?2:%{2}-}modules-extra}\
%defattr(-,root,root)\
/lib/modules/%{KVERREL}%{?2:+%{2}}/extra\
%if %{with_debuginfo}\
%ifnarch noarch\
%{expand:%%files -f debuginfo%{?2}.list %{?2:%{2}-}debuginfo}\
%defattr(-,root,root)\
%endif\
%endif\
%if %{?2:1} %{!?2:0}\
%{expand:%%files %{2}}\
%defattr(-,root,root)\
%endif\
%{nil}


%kernel_variant_files

# plz don't put in a version string unless you're going to tag
# and build.
#
#

%changelog
* Fri Oct 06 2017 Vaughan <devel at agrez dot net> - 4.13.5-1
- Update to stable kernel patch v4.13.5
- Sync RPi patch to git revision: 52cf298f815cb319c999849aece79fa12a5c1970

* Thu Sep 21 2017 Vaughan <devel at agrez dot net> - 4.13.3-1
- Rebase to 4.13 kernel branch
- Update to stable kernel patch v4.13.3
- Sync RPi patch to git revision: 871ca96d47106ef72c54b0ebd6620c8e24343ff0

* Mon Sep 11 2017 Vaughan <devel at agrez dot net> - 4.12.12-1
- Update to stable kernel patch v4.12.12
- Sync RPi patch to git revision: 8f82f552b53e0961f666291b4934e771e3ea6b6a

* Wed Aug 30 2017 Vaughan <devel at agrez dot net> - 4.12.10-1
- Update to stable kernel patch v4.12.10
- Sync RPi patch to git revision: ef79e7bb67c80f0b20a8327692f590a54568eda5

* Mon Aug 21 2017 Vaughan <devel at agrez dot net> - 4.12.8-1
- Rebase to 4.12 kernel branch
- Update to stable kernel patch v4.12.8
- Sync RPi patch to git revision: 0d9ed68fbe6e4e8a5f8a580a211f962304395089
- Build more kernel tools (iio, gpio & kvm_stat)

* Mon Jul 03 2017 Vaughan <devel at agrez dot net> - 4.11.8-1
- Update to stable kernel patch v4.11.8
- Sync RPi patch to git revision: 64b5f5825a998d745801c2682e686423e88a0e93
- Build in CRYPTO_LZ4 & CRYPTO_LZ4HC

* Wed Jun 07 2017 Vaughan <devel at agrez dot net> - 4.11.4-1
- Rebase to 4.11 kernel branch
- Update to stable kernel patch v4.11.4
- Sync RPi patch to git revision: 46d26b7bf221352b299aec39f468df30c4150119
- Disable rt-preempt build support (no patches for 4.11.x series)
- Clean up %%files macro

* Mon Jun 05 2017 Vaughan <devel at agrez dot net> - 4.9.30-2
- Enable support for zSWAP

* Thu Jun 01 2017 Vaughan <devel at agrez dot net> - 4.9.30-1
- Update to stable kernel patch v4.9.30
- Sync RPi patch to git revision: e5bd734340e6871e4e9ef5ff66e61197eb8ece30
- Update to RT PREEMPT kernel v4.9.30-rt20 patchset release

* Fri May 12 2017 Vaughan <devel at agrez dot net> - 4.9.27-1
- Update to stable kernel patch v4.9.27
- Sync RPi patch to git revision: 9a5f215eda12bad29b35040dff00d0346fe517e2

* Sun May 07 2017 Vaughan <devel at agrez dot net> - 4.9.26-1
- Update to stable kernel patch v4.9.26
- Sync RPi patch to git revision: e1a6b0c255dd15be4d32eb4ce1d9301b7c44d7b9

* Tue Apr 25 2017 Vaughan <devel at agrez dot net> - 4.9.24-1
- Update to stable kernel patch v4.9.24
- Sync RPi patch to git revision: dc44db6e247570bc7f3023788b042e5c14a8b4f7

* Tue Apr 11 2017 Vaughan <devel at agrez dot net> - 4.9.21-1
- Update to stable kernel patch v4.9.21
- Sync RPi patch to git revision: 5e4ee836560d4c0371e109bf469e1ad808ae7a44
- Build ipv6 support into kernel

* Tue Apr 04 2017 Vaughan <devel at agrez dot net> - 4.9.20-1
- Update to stable kernel patch v4.9.20
- Sync RPi patch to git revision: 3f53e7886737a975e3fe76bc8ae6cc78f33c8cf8
- Update to RT PREEMPT kernel v4.9.20-rt16 patchset release

* Fri Mar 24 2017 Vaughan <devel at agrez dot net> - 4.9.17-1
- Update to stable kernel patch v4.9.17
- Sync RPi patch to git revision: cd6413a82a66de6ecce828ce67df4f6e3290ea86

* Fri Mar 17 2017 Vaughan <devel at agrez dot net> - 4.9.15-1
- Drop gitshort append from kernel name
- Drop append for 'bcm283x' Flavour with upstream builds
- Append with 'rpi' Flavour for any downstream builds
- Update to stable kernel patch v4.9.15
- Sync RPi patch to git revision: 95452744c5ebcaa0f5d4eaff7313b2b4cd51bd9f

* Tue Mar 14 2017 Vaughan <devel at agrez dot net> - 4.9.14-1
- Update to stable kernel patch v4.9.14
- Sync RPi patch to git revision: a599f69212b051db4cd00a02f9312dc897beba70
- Update main source urls to use https

* Mon Feb 27 2017 Vaughan <devel at agrez dot net> - 4.9.13-1
- Fix bcm283x build (kernel upstream)
- Ensure /boot/.vmlinuz.hmac-%{KVERREL} is removed when uninstalling
- Update to stable kernel patch v4.9.13
- Sync RPi patch to git revision: 883de20e54e16f89a878c9957fd265e352ebf5c3

* Tue Feb 21 2017 Vaughan <devel at agrez dot net> - 4.9.11-1
- Update to stable kernel patch v4.9.11
- Sync RPi patch to git revision: 204050d0eafb565b68abf512710036c10ef1bd23
- Update to RT PREEMPT kernel v4.9.11-rt9 patchset release

* Thu Feb 16 2017 Vaughan <devel at agrez dot net> - 4.9.10-1
- Update to stable kernel patch v4.9.10
- Sync RPi patch to git revision: e4fd443916ed7af63bf1ddb3e01a152a534750bd
- Update to RT PREEMPT kernel v4.9.9-rt6 patchset release

* Fri Feb 10 2017 Vaughan <devel at agrez dot net> - 4.9.9-1
- Update to stable kernel patch v4.9.9
- Sync RPi patch to git revision: a5204ea3b15aa8eaaf2c3c7db7dfb177a84af730
- Use Suggests: linux-firmware
- Update filter-modules.sh

* Sun Feb 05 2017 Vaughan <devel at agrez dot net> - 4.9.8-1
- Update to stable kernel patch v4.9.8
- Sync RPi patch to git revision: 7158cd0f806c91291c4f8e7c2e2b7e5be3023d30
- Update to RT PREEMPT kernel v4.9.6-rt4 patchset release

* Sat Jan 28 2017 Vaughan <devel at agrez dot net> - 4.9.6-1
- Update to stable kernel patch v4.9.6
- Sync RPi patch to git revision: f5ecad4a646f2c06d1e54f3bd52f7bc30004380d
- Update to RT PREEMPT kernel v4.9.4-rt2 patchset release

* Sun Jan 15 2017 Vaughan <devel at agrez dot net> - 4.9.3-1
- Update to stable kernel patch v4.9.3
- Sync RPi patch to git revision: f60564ce83ebf7937e465423e11aa5b5393762ff

* Mon Jan 09 2017 Vaughan <devel at agrez dot net> - 4.9.2-1
- Further improve copying of *.dtb files to /boot after install
- Update to stable kernel patch v4.9.2
- Sync RPi patch to git revision: 8d9edc8eb8c882e312ee57f9464b1a6b43df5b89

* Thu Jan 05 2017 Vaughan <devel at agrez dot net> - 4.9-2
- Update bcm270x.cfg
- Update %%posttrans script
  * Ensure /boot/overlays always exists
  * Be more specific when copying over *.dtb files

* Tue Jan 03 2017 Vaughan <devel at agrez dot net> - 4.9-1
- Rebase to 4.9 kernel branch
- Update to RT PREEMPT kernel v4.9-rt1
- Sync RPi patch to git revision: aa5014ae84c80ceac1561ceb30e060c88d9598d4

* Wed Dec 07 2016 Vaughan <devel at agrez dot net> - 4.8.11-2
- Allow spectool to pull all rt sources / patches

* Thu Dec 01 2016 Damian Wrobel <dwrobel@ertelnet.rybnik.pl> - 4.8.11-1
- Update to stable kernel patch v4.8.11
- Update to RT PREEMPT kernel v4.8.11-rt7

* Wed Nov 23 2016 Damian Wrobel <dwrobel@ertelnet.rybnik.pl> - 4.8.6-2
- Add support for building RT PREEMPT kernel version

* Wed Nov 02 2016 Vaughan <devel at agrez dot net> - 4.8.6-1
- Add build support for bcm2708 kernels
- Update to stable kernel patch v4.8.6
- Sync RPi patch to git revision: 6abac13566786086cd912d87e4f1a922e2a391b2

* Tue Oct 25 2016 Vaughan <devel at agrez dot net> - 4.8.4-1
- Update to stable kernel patch v4.8.4
- Sync RPi patch to git revision: e262d8182b373999a7630ddcafcbbbcc878e64ba

* Sat Oct 15 2016 Vaughan <devel at agrez dot net> - 4.8.1-1
- Rebase to 4.8 kernel branch
- Update to stable kernel patch v4.8.1
- Sync RPi patch to git revision: 5b7970b19bbb2ea1620591bfb6517848696ed0b9
- Use kernel config fragments file for bcm283x builds (as per the bcm2709 build)
- Update how patches are applied for each build
- Rename patches 10 & 100

* Sat Sep 17 2016 Vaughan <devel at agrez dot net> - 4.7.4-1
- Update to stable kernel patch v4.7.4
- Sync RPi patch to git revision: 3e1b1adce79b673ef890cf5a7379697c5b4ba724

* Mon Sep 12 2016 Vaughan <devel at agrez dot net> - 4.7.3-1
- Rebase to 4.7.y kernel branch
- Update to stable kernel patch v4.7.3
- Sync RPi patch to git revision: cb03c80f44aeff4dfb8930bee5bbfbd032d07f0a
- Add custom FedBerry boot logo
- Enable SECCOMP filter options and CONFIG_AUDITSYSCALL
- Add grubby to kernel_prereq (it provides /sbin/new-kernel-pkg)
- Fix copying of .dbto's to /boot/overlays/

* Thu Aug 11 2016 Vaughan <devel at agrez dot net> - 4.6.6-1
- Rebase to 4.6.y kernel branch
- Update to stable kernel patch v4.6.6
- Sync RPi patch to git revision: 2d4bf9aeaa3c6b002520ee37555d49d8a495bf20
- RasperryPi foundation patch name should be using %%{base_sublevel}

* Thu Aug 11 2016 Vaughan <devel at agrez dot net> - 4.5.7-1
- Split bcm2709 linux kernel port into a separate build option (enabled by default)
- Add a new kernel config for kernel.org (bcm2835) builds (bcm283x.config)
- Add mkknlimg to the bcm283x build (Patch10)
- vmlinuz, System.map, config & .hmac files now installed to '/lib/modules/$KernelVer/'
- Updated kernel %%files & %%posttrans to relfect relocation of kernel files
- Sync RPi patch to git revision: 237402141fd74ca989bd86ebb76d834cb6fa5454
- Update to stable kernel patch v4.5.7
- Misc spec file cleanups

* Sun Mar 20 2016 Vaughan <devel at agrez dot net> - 4.5.0-1.d553aa6
- Modify how we apply patches
- Rebase to 4.5.y kernel branch
- Sync RPi patch to git revision: rpi-4.5.y d553aa6b15b40562813eb5c0d1b640fb83e8fc50
- Kernel now enables by default Device Tree Overlay ConfigFS interface (*.dtbo files)
  Refer: https://github.com/raspberrypi/linux/commit/d95dcfb60819ec448273853e027766bdb241869c
  Refer: https://www.raspberrypi.org/forums/viewtopic.php?f=107&t=139732
- Add Requires: raspberrypi-vc-utils >= 20160321 (kernel now requires dtoverlay util)

* Fri Mar 11 2016 Vaughan <devel at agrez dot net> - 4.4.5-400.418177e
- Sync RPi patch to git revision: rpi-4.4.y 418177e2e57d3ac1248ced154fa1067ca42ba315
- Update to stable kernel patch v4.4.5

* Tue Mar 08 2016 Vaughan <devel at agrez dot net> - 4.4.4-401.4f7b097
- Sync RPi patch to git revision: rpi-4.4.y 4f7b097a399b7d0ed275bca0ec72fb4d05c4094b
- Clean /boot/overlays in %%posttrans to remove any stale *.dtb files.
- Copy everything to /boot/overlays (not just .dbt files).

* Mon Mar 07 2016 Vaughan <devel at agrez dot net> - 4.4.4-400.c5cbb66
- Sync RPi patch to git revision: rpi-4.4.y c5cbb66686e7e289e8a7aff49a954f86893e628d
- Stable kernel.org patch now referenced as a Source1
- Stable patch now applied directly instead of using ApplyPatch() function

* Wed Mar 02 2016 Vaughan <devel at agrez dot net> - 4.4.3-401.36babd8
- Sync patch to RPi git revision: rpi-4.4.y 36babd89241c85258acebe06616f1f1a58356f8e
- Add RPi 3 Model B support (bcm2710)

* Sun Feb 28 2016 Vaughan <devel at agrez dot net> - 4.4.3-400.8547bb0
- Update to stable kernel patch v4.4.3
- Sync patch to RPi git revision: rpi-4.4.y 8547bb07f9d79874648c6a4aab545fbabe0b4765

* Sat Feb 20 2016 Vaughan <devel at agrez dot net> - 4.4.2-400.8941fe4
- Update to stable kernel patch v4.4.2
- Sync patch to RPi git revision: rpi-4.4.y 8941fe4985a1cc8f800be00224c6a2e741789d03

* Sun Feb 14 2016 Vaughan <devel at agrez dot net> - 4.4.1-401.52d3149
- Sync patch to RPi git revision: rpi-4.4.y 52d3149aba3c684db1b6c739ca794dc330d92929
  This includes the significant revision of the bcm2835-sdhost driver

* Tue Feb 09 2016 Vaughan <devel at agrez dot net> - 4.4.1-400.065d2a9
- Rebase to 4.4.y kernel branch
- Update to stable kernel patch v4.4.1
- Sync patch to RPi git revision: rpi-4.4.y 065d2a9ca6e18a16431ced57a40dddc06b792650

* Sun Jan 24 2016 Vaughan <devel at agrez dot net> - 4.3.4-400.4dee941
- Update to stable kernel patch v4.3.4
- Sync rpi patch to git revision: rpi-4.3.y 4dee9412d72abd346c9b7a3bbd8e96a5f0b163f3

* Sat Jan 16 2016 Vaughan <devel at agrez dot net> - 4.3.3-400.547120c
- Rebase to 4.3.y kernel branch
- Update to stable kernel patch v4.3.3
- Sync patch to git revision: rpi-4.3.y 547120c6be9054cd4b7186aee95c6e698f839d44

* Wed Dec 23 2015 Vaughan <devel at agrez dot net> - 4.2.8-400.e0103e9
- Update to stable kernel patch v4.2.8
- Sync patch to git revision: rpi-4.2.y e0103e9645caca6576c1b6c21608c28015857ab8
- Split out config modifications to config-fedberry.cfg
- Apply config 'fragments' (config-fedberry.cfg) at build time using 'merge_config.sh'
- Drop config-bcm2709
- Enable PREEMPT_VOLUNTARY
- Refactor kernel config

* Sat Dec 12 2015 Vaughan <devel at agrez dot net> - 4.2.7-400.c35cc1f
- Sync patch to git revision: rpi-4.2.y c35cc1fea33fcbaa04ddcd8c9733fd66f6d3e7ad
- Update to stable kernel patch v4.2.7
- Drop kbuild-AFTER_LINK.patch as its not used.
- Add TOUCHSCREEN_FT6236=m

* Sat Dec 05 2015 Vaughan <devel at agrez dot net> - 4.2.6-402.806e022
- Disable NFSv2 support
- Enable NFSv4_1 & NFSv4_2 support
- Build NFSD as a module (NFSD=m)

* Sun Nov 29 2015 Vaughan <devel at agrez dot net> - 4.2.6-401.806e022
- Sync patch to git revision: rpi-4.2.y 806e02221caec4ca42adc7aed42f5523bc8fb0dc
- Disable initrd creation for now (we currently don't use it)

* Sun Nov 15 2015 Vaughan <devel at agrez dot net> - 4.2.6-400.429f50d
- Sync patch to git revision: rpi-4.2.y 429f50d21465619822725e5134f51e4782dec4fe
- Update to stable kernel patch v4.2.6

* Sat Oct 31 2015 Vaughan <devel at agrez dot net> - 4.2.5-400.50acac3
- Sync patch to git revision: rpi-4.2.y 50acac3fd0a949f6cd15cdfaac9e2e1588aada0b
- Update to stable kernel patch v4.2.5
- Refactor kernel config

* Wed Oct 14 2015 Vaughan <devel at agrez dot net> - 4.2.3-401.6c1c048
- Sync patch to git revision: rpi-4.2.y 6c1c04868e77b2ff314b42548b12963d824230f8
- Default bcm2709 kernel config (bcm2709_defconfig) does not enable selinux
  support. Enable it!
- Refactor kernel config

* Wed Oct 07 2015 Vaughan <devel at agrez dot net> - 4.2.3-400.30fc66b
- Rebase to 4.2.y kernel branch
- Update to stable kernel patch v4.2.3
- Sync patch to git revision: rpi-4.2.y 30fc66bfd7a538fb620c3b7bc4daaf79f8d92d70
- Refactor kernel config

* Mon Oct 05 2015 Vaughan <devel at agrez dot net> - 4.1.10-300.0b43921
- Update to stable kernel patch v4.1.10
- Sync to latest git revision: rpi-4.1.y 0b439214b09e3f80413c19b7e0a407c34a79411c

* Thu Sep 24 2015 Vaughan <devel at agrez dot net> - 4.1.8-300.d2b2388
- Update to stable kernel patch v4.1.8
- Sync to latest git revision: rpi-4.1.y d2b2388d05d8a97b0ba14fcf2b71f19f66bc4d02

* Thu Sep 17 2015 Vaughan <devel at agrez dot net> - 4.1.7-300.676d8d9
- Update to stable kernel patch v4.1.7
- Sync to latest git revision: rpi-4.1.y 676d8d98ed6ffa1afce9cd6585017db8fe606347
- Refactor kernel config
- install_dtbs target now works correctly, modify spec accordingly.

* Fri Sep 11 2015 Vaughan <devel at agrez dot net> - 4.1.6-302.c8baa97
- Sync to latest git revision: rpi-4.1.y c8baa9702cc99de9614367d0b96de560944e7ccd
- Requires bcm283x-firmware >= 20150909

* Wed Sep 02 2015 Vaughan <devel at agrez dot net> - 4.1.6-301.6b30ac8
- Sync to latest git revision: rpi-4.1.y 6b30ac82c3595887416c7870c35c2cc522f801cc 
- Refactor kernel config

* Wed Aug 19 2015 Vaughan <devel at agrez dot net> - 4.1.6-300.4507c97
- Update to stable kernel patch v4.1.6
- Sync to latest git revision: rpi-4.1.y 4507c9752292506fa6ef136114ad14ffd92b2ca5
- Requires bcm283x-firmware >= 20150819
- Refactor kernel config

* Tue Aug 18 2015 Vaughan <devel at agrez dot net> - 4.1.5-301.5925037
- Drop the extra generated kernel-*.img
- Add device tree trailer to vmlinuz image instead 

* Sun Aug 16 2015 Vaughan <devel at agrez dot net> - 4.1.5-300.5925037
- Sync to latest git revision: rpi-4.1.y 592503752b6951972f161f04280683c5af38d173
- Requires bcm283x-firmware >= 20150815

* Sun Aug 16 2015 Vaughan <devel at agrez dot net> - 4.1.5-300.5925037
- Sync to latest git revision: rpi-4.1.y 592503752b6951972f161f04280683c5af38d173
- Requires bcm283x-firmware >= 20150815

* Sat Aug 08 2015 Vaughan <devel at agrez dot net> - 4.1.4-300.869c3bc
- Update to stable kernel release v4.1.4
- Sync to latest rpi git revision: rpi-4.1.y 869c3bc300150a8afd4bc42efcb0f36f0b041f09
- Requires bcm283x-firmware >= 20150808-11eaffc

* Sat Jul 25 2015 Vaughan <devel at agrez dot net> - 4.0.9-300.4d317a8
- Update to stable kernel release v4.0.9
- Sync to latest rpi git revision: rpi-4.0.y 4d317a835a7b6354e41c2678507f2a894fdceb26
- Requires bcm283x-firmware >= 20150725-1.464ce4f

* Wed Jul 15 2015 Vaughan <devel at agrez dot net> - 4.0.8-300.4259dcc
- Update to stable kernel release v4.0.8
- Sync to latest rpi git revision: rpi-4.0.y 4259dcc8987bd0d88428762c637a18df553de04c
- Refactor kernel config

* Tue Jun 30 2015 Vaughan <devel at agrez dot net> - 4.0.7-300.c53bd46
- Fork from current Fedora spec and make it build on the RaspberryPi 2.
  This involved numermous modifications / changes (too many to list).
- This is a dedicated spec file for building Raspberry Pi 2 kernels only.
  No other arm platforms are presently supported.
- Strip support for all other archs and kernel build types.
- Drop most additional 'fedora' patches
- Update to stable kernel release v4.0.7
- Sync to latest rpi git revision: rpi-4.0.y c53bd4659ef8b3e8161a85f297b93a9408226b6a
  (Patch100)
- Refactor kernel config (config-bcm2709)
- Add requires for bcm283x-firmware >= 20150620-1.8b9d7b (kernel-core)

* Tue Jun 23 2015 Justin M. Forbes <jforbes@fedoraproject.org> - 4.0.6-300
- Linux v4.0.6

* Thu Jun 18 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Add patch to fix touchpad issues on Razer machines (rhbz 1227891)

* Fri Jun 12 2015 Josh Boyer <jwboyer@fedoraproject.org>
- CVE-2015-XXXX kvm: NULL ptr deref in kvm_apic_has_events (rhbz 1230770 1230774)

* Thu Jun 11 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Backport fixes for synaptic 3 finger tap (rhbz 1212230)
- Backport btrfs fixes queued for stable (rhbz 1217191)

* Tue Jun 09 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Fix touchpad for Thinkpad S540 (rhbz 1223051)

* Mon Jun 08 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Linux v4.0.5

* Thu Jun 04 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Backport commit to fix block spew (rhbz 1226621)
- Add patch to fix SMT guests on POWER7 (rhbz 1227877)
- Add patch to turn of WC mmaps on i915 from airlied (rhbz 1226743)

* Wed Jun 03 2015 Laura Abbott <labbott@fedoraproject.org>
- Fix del_timer_sync in mwifiex

* Wed Jun 03 2015 Laura Abbott <labbott@fedoraproject.org>
- Drop that blasted firwmare warning until we get a real fix (rhbz 1133378)

* Wed Jun 03 2015 Laura Abbott <labbott@fedoraproject.org>
- Fix auditing of canonical mode (rhbz 1188695)

* Wed Jun 03 2015 Josh Boyer <jwboyer@fedoraproject.org>
- CVE-2015-1420 fhandle race condition (rhbz 1187534 1227417)

* Tue Jun 02 2015 Laura Abbott <labbott@fedoraproject.org>
- Fix fd_do_rw error (rhbz 1218882)

* Tue Jun 02 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Fix middle button issues on external Lenovo keyboards (rhbz 1225563)

* Thu May 28 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Add quirk for Mac Pro backlight (rhbz 1217249)

* Thu May 28 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.4-303
- Add patch to avoid vmmouse being classified as a joystic (rhbz 1214474)

* Wed May 27 2015 Josh Boyer <jwboyer@fedoraproject.org> -4.0.4-302
- Apply queued fixes for crasher reported by Alex Larsson
- Enable in-kernel vmmouse driver (rhbz 1214474)

* Tue May 26 2015 Laura Abbott <labbott@fedoraproject.org>
- Fix signed division error (rhbz 1200353)

* Tue May 26 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Backport patch to fix might_sleep splat (rhbz 1220519)

* Thu May 21 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.4-301
- Add patch to fix discard on md RAID0 (rhbz 1223332)
- Add submitted stable fix for i915 flickering on ilk (rhbz 1218688)

* Mon May 18 2015 Laura Abbott <labbott@fedoraproject.org>
- Re-add the v4l2 query caps patch which was dropped

* Mon May 18 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Fix incorrect bandwidth on some Chicony webcams

* Mon May 18 2015 Justin M. Forbes <jforbes@fedoraproject.org> - 4.0.4-300
- Linux v4.0.4

* Fri May 15 2015 Laura Abbott <labbott@fedoraproject.org>
- Fix DVB oops (rhbz 1220118)

* Thu May 14 2015 Justin M. Forbes <jforbes@fedoraproject.org> - 4.0.3-301
- Disable i915 verbose state checks

* Thu May 14 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Fix non-empty dir removal in overlayfs (rhbz 1220915)

* Wed May 13 2015 Laura Abbott <labbott@fedoraproject.org>
- Fix spew from KVM switch (rhbz 1219343)

* Wed May 13 2015 Justin M. Forbes <jforbes@fedoraproject.org> - 4.0.3-300
- Linux v4.0.3

* Sat May  9 2015 Peter Robinson <pbrobinson@fedoraproject.org>
- Minor ARMv7 updates

* Thu May 07 2015 Justin M. Forbes <jforbes@fedoraproject.org> - 4.0.2-300
- Linux v4.0.2 (rhbz 1182816)

* Tue May 05 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Backport patch to blacklist TRIM on all Samsung 8xx series SSDs (rhbz 1218662)
- CVE-2015-3636 ping-sockets use-after-free privilege escalation (rhbz 1218074 1218110)

* Thu Apr 30 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Fix backlight on various Toshiba machines (rhbz 1206036 1215989)

* Wed Apr 29 2015 Justin M. Forbes <jforbes@fedoraproject.org> - 4.0.1-300
- Linux v4.0.1

* Tue Apr 28 2015 Justin M. Forbes <jforbes@fedoraproject.org>
- Fix up boot times for live images (rhbz 1210857)

* Mon Apr 27 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Backport NFS DIO fixes from 4.1 (rhbz 1211017 1211013)

* Fri Apr 24 2015 Josh Boyer <jwboyer@fedoraproject.org>
- CVE-2015-3339 race condition between chown and execve (rhbz 1214030)
- Fix iscsi with QNAP devices (rhbz 1208999)

* Wed Apr 22 2015 Peter Robinson <pbrobinson@fedoraproject.org>
- Fix RTC on TrimSlice
- Enable all sound modules for TrimSlice (also needed for other devices)

* Mon Apr 20 2015 Laura Abbott
- Fix sound issues (rhbz 1188741)

* Fri Apr 17 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Add support for touchpad on Google Pixel 2 (rhbz 1209088)
- Allow disabling raw mode in logitech-hidpp (rhbz 1210801)

* Wed Apr 15 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Add patch to fix tty closure race (rhbz 1208953)

* Sun Apr 12 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-1
- Linux v4.0

* Fri Apr 10 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc7.git2.1
- Linux v4.0-rc7-42-ge5e02de0665e

* Thu Apr 09 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc7.git1.1
- Linux v4.0-rc7-30-g20624d17963c

* Thu Apr 02 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc6.git2.1
- Linux v4.0-rc6-101-g0a4812798fae

* Thu Apr 02 2015 Josh Boyer <jwboyer@fedoraproject.org>
- DoS against IPv6 stacks due to improper handling of RA (rhbz 1203712 1208491)

* Wed Apr 01 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc6.git1.1
- Linux v4.0-rc6-31-gd4039314d0b1
- CVE-2015-2150 xen: NMIs triggerable by guests (rhbz 1196266 1200397)

* Tue Mar 31 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Enable MLX4_EN_VXLAN (rhbz 1207728)

* Mon Mar 30 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc6.git0.1
- Linux v4.0-rc6

* Fri Mar 27 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc5.git4.1
- Linux v4.0-rc5-96-g3c435c1e472b
- Fixes hangs due to i915 issues (rhbz 1204050 1206056)

* Thu Mar 26 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc5.git3.1
- Linux v4.0-rc5-80-g4c4fe4c24782

* Wed Mar 25 2015 Peter Robinson <pbrobinson@fedoraproject.org>
- Add aarch64 patches to fix mustang usb, seattle eth, and console settings

* Wed Mar 25 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc5.git2.4
- Add patches to fix a few more i915 hangs/oopses

* Wed Mar 25 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc5.git2.1
- Linux v4.0-rc5-53-gc875f421097a

* Tue Mar 24 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Fix ALPS v5 and v7 trackpads (rhbz 1203584)

* Tue Mar 24 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc5.git1.3
- Linux v4.0-rc5-25-g90a5a895cc8b
- Add some i915 fixes

* Mon Mar 23 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc5.git0.3
- Enable CONFIG_SND_BEBOB (rhbz 1204342)
- Validate iovec range in sys_sendto/sys_recvfrom
- Revert i915 commit that causes boot hangs on at least some headless machines
- Linux v4.0-rc5

* Fri Mar 20 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc4.git2.1
- Linux v4.0-rc4-199-gb314acaccd7e
- Fix brightness on Lenovo Ideapad Z570 (rhbz 1187004)

* Thu Mar 19 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc4.git1.3
- Linux v4.0-rc4-88-g7b09ac704bac
- Rename arm64-xgbe-a0.patch

* Thu Mar 19 2015 Peter Robinson <pbrobinson@fedoraproject.org>
- Drop arm64 non upstream patch

* Thu Mar 19 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Add patch to fix high cpu usage on direct_read kernfs files (rhbz 1202362)

* Wed Mar 18 2015 Jarod Wilson <jwilson@fedoraproject.org>
- Fix kernel-uname-r Requires/Provides variant mismatches

* Tue Mar 17 2015 Kyle McMartin <kmcmarti@redhat.com> - 4.0.0-0.rc4.git0.3
- Update kernel-arm64.patch, move EDAC to arm-generic, add EDAC_XGENE on arm64.
- Add PCI_ECAM on generic, since it'll be selected most places anyway.

* Mon Mar 16 2015 Jarod Wilson <jwilson@fedoraproject.org>
- Fix bad variant usage in kernel dependencies

* Mon Mar 16 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc4.git0.1
- Linux v4.0-rc4
- Drop arm64 RCU revert patch.  Should be fixed properly upstream now.
- Disable debugging options.

* Sun Mar 15 2015 Jarod Wilson <jwilson@fedoraproject.org>
- Fix kernel-tools sub-packages for variant builds

* Fri Mar 13 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Fix esrt build on aarch64

* Fri Mar 13 2015 Kyle McMartin <kyle@fedoraproject.org>
- arm64-revert-tlb-rcu_table_free.patch: revert 5e5f6dc1 which
  causes lockups on arm64 machines.
- Also revert ESRT on AArch64 for now.

* Fri Mar 13 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc3.git2.1
- Linux v4.0-rc3-148-gc202baf017ae
- Add patch to support clickpads (rhbz 1201532)

* Thu Mar 12 2015 Josh Boyer <jwboyer@fedoraproject.org>
- CVE-2014-8159 infiniband: uverbs: unprotected physical memory access (rhbz 1181166 1200950)

* Wed Mar 11 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc3.git1.1
- Linux v4.0-rc3-111-gaffb8172de39
- CVE-2015-2150 xen: NMIs triggerable by guests (rhbz 1196266 1200397)
- Patch series to fix Lenovo *40 and Carbon X1 touchpads (rhbz 1200777 1200778)
- Revert commit that added bad rpath to cpupower (rhbz 1199312)
- Reenable debugging options.

* Mon Mar 09 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc3.git0.1
- Linux v4.0-rc3
- Disable debugging options.

* Sun Mar  8 2015 Peter Robinson <pbrobinson@fedoraproject.org>
- ARMv7: add patches to fix crash on boot for some devices on multiplatform

* Fri Mar 06 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc2.git2.1
- Linux v4.0-rc2-255-g5f237425f352

* Thu Mar 05 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc2.git1.1
- Linux v4.0-rc2-150-g6587457b4b3d
- Reenable debugging options.

* Wed Mar 04 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Enable MLX4_EN on ppc64/aarch64 (rhbz 1198719)

* Tue Mar 03 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc2.git0.1
- Linux v4.0-rc2
- Enable CONFIG_CM32181 for ALS on Carbon X1
- Disable debugging options.

* Tue Mar 03 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc1.git3.1
- Linux v4.0-rc1-178-g023a6007a08d

* Mon Mar 02 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Add patch to fix nfsd soft lockup (rhbz 1185519)
- Enable ET131X driver (rhbz 1197842)
- Enable YAMA (rhbz 1196825)

* Sat Feb 28 2015 Peter Robinson <pbrobinson@fedoraproject.org>
- ARMv7 OMAP updates, fix panda boot

* Fri Feb 27 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc1.git2.1
- Linux v4.0-rc1-36-g4f671fe2f952

* Wed Feb 25 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Add support for AR5B195 devices from Alexander Ploumistos (rhbz 1190947)

* Tue Feb 24 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc1.git1.1
- Linux v4.0-rc1-22-gb24e2bdde4af
- Reenable debugging options.

* Tue Feb 24 2015 Richard W.M. Jones <rjones@redhat.com> - 4.0.0-0.rc1.git0.2
- Add patch to fix aarch64 KVM bug with module loading (rhbz 1194366).

* Tue Feb 24 2015 Peter Robinson <pbrobinson@fedoraproject.org>
- Minor ARM config update

* Mon Feb 23 2015 Josh Boyer <jwboyer@fedoraproject.org> - 4.0.0-0.rc1.git0.1
- Add patch for HID i2c from Seth Forshee (rhbz 1188439)

* Mon Feb 23 2015 Josh Boyer <jwboyer@fedoraproject.org>
- Linux v4.0-rc1
- CVE-2015-0275 ext4: fallocate zero range page size > block size BUG (rhbz 1193907 1195178)
- Disable debugging options.

###
# The following Emacs magic makes C-c C-e use UTC dates.
# Local Variables:
# rpm-change-log-uses-utc: t
# End:
###
