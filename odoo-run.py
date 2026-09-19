__import__('os').environ['TZ'] = 'UTC'
import odoo.cli

if __name__ == "__main__":
    odoo.cli.main()
