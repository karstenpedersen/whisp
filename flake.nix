{
  description = "Whisper";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    systems.url = "github:nix-systems/default";
    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = {
    self,
    nixpkgs,
    systems,
    treefmt-nix,
  }: let
    eachSystem = f: nixpkgs.lib.genAttrs (import systems) (system: f nixpkgs.legacyPackages.${system});
    treefmtEval = eachSystem (pkgs:
      treefmt-nix.lib.evalModule pkgs {
        projectRootFile = "flake.nix";
        programs = {
          alejandra.enable = true;
          ruff-format.enable = true;
        };
      });
  in {
    formatter = eachSystem (pkgs: treefmtEval.${pkgs.system}.config.build.wrapper);
    checks = eachSystem (pkgs: {
      formatting = treefmtEval.${pkgs.system}.config.build.check self;
    });
    devShells = eachSystem (pkgs: {
      default = pkgs.mkShell {
        packages = [
          pkgs.python313
          pkgs.uv
          pkgs.just
          pkgs.portaudio
          treefmtEval.${pkgs.system}.config.build.wrapper
        ];

        UV_PYTHON = "${pkgs.python313}/bin/python";
        UV_PYTHON_DOWNLOADS = "never";

        LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
          pkgs.portaudio
          pkgs.stdenv.cc.cc.lib
          pkgs.zlib
        ];
      };
    });
  };
}
