"""cli_signature.py — CLI commands for signing and verifying snapshots."""

from __future__ import annotations

import argparse
import sys

from envcage.env_signature import sign_snapshot_file, verify_snapshot_file


def cmd_signature_sign(args: argparse.Namespace) -> None:
    """Sign a snapshot file and embed the HMAC signature."""
    result = sign_snapshot_file(
        path=args.snapshot,
        passphrase=args.passphrase,
        output=getattr(args, "output", None),
    )
    print(f"Signed: {result.snapshot_path}")
    print(f"Signature: {result.signature}")


def cmd_signature_verify(args: argparse.Namespace) -> None:
    """Verify the embedded signature of a snapshot file."""
    result = verify_snapshot_file(
        path=args.snapshot,
        passphrase=args.passphrase,
    )
    if result.valid:
        print(f"OK: Signature is valid for {result.snapshot_path}")
        sys.exit(0)
    else:
        print(f"FAIL: {result.reason} ({result.snapshot_path})", file=sys.stderr)
        sys.exit(1)


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    # --- sign ---
    p_sign = subparsers.add_parser(
        "signature-sign",
        help="Sign a snapshot file with an HMAC passphrase.",
    )
    p_sign.add_argument("snapshot", help="Path to the snapshot JSON file.")
    p_sign.add_argument("passphrase", help="Passphrase used to derive the HMAC key.")
    p_sign.add_argument(
        "--output",
        default=None,
        help="Optional output path (defaults to overwriting the input file).",
    )
    p_sign.set_defaults(func=cmd_signature_sign)

    # --- verify ---
    p_verify = subparsers.add_parser(
        "signature-verify",
        help="Verify the embedded HMAC signature of a snapshot file.",
    )
    p_verify.add_argument("snapshot", help="Path to the signed snapshot JSON file.")
    p_verify.add_argument("passphrase", help="Passphrase used when the snapshot was signed.")
    p_verify.set_defaults(func=cmd_signature_verify)
