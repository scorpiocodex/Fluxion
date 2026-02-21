class Fluxion < Formula
  include Language::Python::Virtualenv

  desc "The Intelligent Network Command Engine"
  homepage "https://github.com/fluxion-net/fluxion"
  url "https://github.com/fluxion-net/fluxion/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "PLACEHOLDER"
  license "MIT"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "0.1.0", shell_output("#{bin}/fluxion version")
  end
end
